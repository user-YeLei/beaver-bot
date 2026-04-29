"""Beaver Bot Data Store - User/System data separation and migration"""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from packaging import version as pkg_version

import structlog

logger = structlog.get_logger()


@dataclass
class DataVersion:
    """Represents a data version"""
    raw: str
    
    def __post_init__(self):
        self.raw = self.raw.strip()
        try:
            self._parsed = pkg_version.parse(self.raw)
        except Exception:
            self._parsed = pkg_version.parse(self.raw.split('-')[0])
    
    def __str__(self) -> str:
        return self.raw
    
    def __repr__(self) -> str:
        return f"DataVersion({self.raw})"
    
    def _compare(self, other: "DataVersion", op) -> bool:
        if not isinstance(other, DataVersion):
            return NotImplemented
        return op(self._parsed, other._parsed)
    
    def __lt__(self, other: "DataVersion") -> bool:
        return self._compare(other, lambda s, o: s < o)
    
    def __le__(self, other: "DataVersion") -> bool:
        return self._compare(other, lambda s, o: s <= o)
    
    def __gt__(self, other: "DataVersion") -> bool:
        return self._compare(other, lambda s, o: s > o)
    
    def __ge__(self, other: "DataVersion") -> bool:
        return self._compare(other, lambda s, o: s >= o)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataVersion):
            return False
        return self.raw == other.raw
    
    def __hash__(self) -> int:
        return hash(self.raw)


@dataclass
class DataCategory:
    """Category of data with retention strategy"""
    name: str
    path: Path
    retention: str  # "user" | "system" | "always_keep"
    description: str = ""


@dataclass 
class Migration:
    """A single migration"""
    version: DataVersion
    name: str
    description: str
    migrate_fn: Callable[["DataStore"], bool]


@dataclass
class DataStore:
    """
    Data store with user/system data separation.
    
    Directory structure:
        data/
        ├── .version           # Current data version
        ├── .applied_migrations # List of applied migrations
        ├── logs/              # Conversation logs (always_keep)
        ├── config/
        │   ├── settings.yaml  # System config (overwrite on upgrade)
        │   └── .user.yaml     # User overrides (keep)
        └── skills/
            ├── builtin/       # System skills (overwrite on upgrade)
            │   ├── grill-me/
            │   ├── tdd/
            │   └── ...
            └── user/          # User skills (always_keep)
                └── my-skill/
    
    Retention strategies:
        - user: User data, never touched by migrations
        - system: System data, can be overwritten on upgrade
        - always_keep: Always preserved, even across major upgrades
    """
    
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    
    def __post_init__(self):
        # Core paths
        self.data_dir = self.project_root / "data"
        self.version_file = self.data_dir / ".version"
        self.applied_file = self.data_dir / ".applied_migrations"
        
        # Data category paths
        self.logs_dir = self.data_dir / "logs"
        self.config_dir = self.data_dir / "config"
        self.skills_builtin = self.data_dir / "skills" / "builtin"
        self.skills_user = self.data_dir / "skills" / "user"
        
        # Legacy paths (for migration from old structure)
        self.legacy_logs = self.project_root / "logs"
        self.legacy_skills = self.project_root / "skills"
        self.legacy_config = self.project_root / "config"
        
        # Ensure directories
        self._ensure_dirs()
        
        # Migration registry
        self._migrations: Dict[str, Migration] = {}
        self._register_builtin_migrations()
    
    def _ensure_dirs(self) -> None:
        """Ensure all data directories exist"""
        for d in [self.data_dir, self.logs_dir, self.config_dir,
                  self.skills_builtin, self.skills_user]:
            d.mkdir(parents=True, exist_ok=True)
    
    # ─────────────────────────────────────────────────────────
    # Version Management
    # ─────────────────────────────────────────────────────────
    
    def get_version(self) -> DataVersion:
        """Get current data version"""
        if not self.version_file.exists():
            return DataVersion("0.0.0")
        return DataVersion(self.version_file.read_text().strip())
    
    def set_version(self, ver: str) -> None:
        """Set current data version"""
        self.version_file.write_text(ver.strip())
        logger.info("data_version_set", version=ver)
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names"""
        if not self.applied_file.exists():
            return []
        try:
            content = self.applied_file.read_text().strip()
            return json.loads(content) if content else []
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_applied(self, names: List[str]) -> None:
        """Save applied migration list"""
        self.applied_file.write_text(json.dumps(names, indent=2))
    
    # ─────────────────────────────────────────────────────────
    # Migration System
    # ─────────────────────────────────────────────────────────
    
    def _register_builtin_migrations(self) -> None:
        """Register built-in migrations"""
        # v0.1.0: Initial version with user/system separation
        self._migrations["0.1.0"] = Migration(
            DataVersion("0.1.0"),
            "initial_user_system_separation",
            "Initial user/system data separation",
            self._migrate_initial
        )
        
        # v0.2.0: Add structured skill format
        self._migrations["0.2.0"] = Migration(
            DataVersion("0.2.0"),
            "add_structured_skill_format", 
            "Add phases/steps/checklist to skills",
            self._migrate_structured_skills
        )
    
    def register_migration(self, version: str, name: str, description: str,
                           fn: Callable[["DataStore"], bool]) -> None:
        """Register a new migration (for extensions)"""
        self._migrations[version] = Migration(
            DataVersion(version), name, description, fn
        )
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that need to run"""
        current = self.get_version()
        applied = self.get_applied_migrations()
        
        pending = []
        for ver_str, migration in sorted(self._migrations.items(),
                                          key=lambda x: DataVersion(x[0])):
            if migration.name in applied:
                continue
            if DataVersion(ver_str) <= current:
                continue
            pending.append(migration)
        
        return sorted(pending, key=lambda x: x.version)
    
    def migrate(self) -> bool:
        """
        Run all pending migrations.
        Returns True if all succeeded or nothing to do.
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("no_pending_migrations", 
                       version=str(self.get_version()))
            return True
        
        logger.info("starting_migrations", count=len(pending),
                   from_version=str(self.get_version()))
        
        applied = self.get_applied_migrations()
        
        for migration in pending:
            logger.info("running_migration",
                        version=str(migration.version),
                        name=migration.name,
                        description=migration.description)
            
            try:
                success = migration.migrate_fn(self)
            except Exception as e:
                logger.error("migration_failed",
                           version=str(migration.version),
                           name=migration.name,
                           error=str(e))
                return False
            
            if not success:
                logger.error("migration_returned_false",
                           version=str(migration.version),
                           name=migration.name)
                return False
            
            applied.append(migration.name)
            self._save_applied(applied)
            self.set_version(str(migration.version))
            
            logger.info("migration_success",
                       version=str(migration.version),
                       name=migration.name)
        
        logger.info("all_migrations_complete",
                   final_version=str(self.get_version()))
        return True
    
    # ─────────────────────────────────────────────────────────
    # Built-in Migrations
    # ─────────────────────────────────────────────────────────
    
    def _migrate_initial(self) -> bool:
        """
        v0.1.0: Initial migration - set up user/system separation.
        
        Copies existing data to new structure if it exists.
        """
        # Migrate logs from legacy location
        if self.legacy_logs.exists():
            for f in self.legacy_logs.glob("*.jsonl"):
                dest = self.logs_dir / f.name
                if not dest.exists():
                    shutil.copy2(f, dest)
                    logger.info("migrated_log_file", source=str(f), dest=str(dest))
        
        # Migrate skills - builtin vs user based on location
        if self.legacy_skills.exists():
            for skill_path in self.legacy_skills.iterdir():
                if not skill_path.is_dir():
                    continue
                    
                # Check if it looks like a user-added skill
                # Heuristic: if skill was in legacy dir before, treat as builtin
                # But user skills in skills/user/ should remain user
                dest_builtin = self.skills_builtin / skill_path.name
                dest_user = self.skills_user / skill_path.name
                
                if skill_path.name in ["grill-me", "tdd", "vertical-slice", "refactor"]:
                    # These are known system skills - move to builtin
                    if not dest_builtin.exists():
                        shutil.copytree(skill_path, dest_builtin)
                        logger.info("migrated_builtin_skill", name=skill_path.name)
                else:
                    # Unknown skill - treat as user
                    if not dest_user.exists():
                        shutil.copytree(skill_path, dest_user)
                        logger.info("migrated_user_skill", name=skill_path.name)
        
        # Migrate config
        if self.legacy_config.exists():
            settings = self.legacy_config / "settings.yaml"
            if settings.exists():
                dest = self.config_dir / "settings.yaml"
                if not dest.exists():
                    shutil.copy2(settings, dest)
                    logger.info("migrated_config", source=str(settings), dest=str(dest))
        
        # Mark legacy dirs as migrated (but don't delete - keep for rollback)
        (self.data_dir / ".legacy_migrated").write_text("true")
        
        return True
    
    def _migrate_structured_skills(self) -> bool:
        """
        v0.2.0: Add structured skill format (phases/steps/checklist).
        
        Updates skill format while preserving user skills unchanged.
        """
        # This migration only affects builtin skills
        # User skills keep their format
        if not self.skills_builtin.exists():
            return True
        
        for skill_path in self.skills_builtin.iterdir():
            if not skill_path.is_dir():
                continue
            
            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                continue
            
            # Check if already has new format
            content = skill_md.read_text()
            if "phases:" in content or "steps:" in content:
                # Already updated or is legacy format with steps
                continue
            
            logger.info("skill_needs_update", skill=skill_path.name)
            # Skill needs format update - this would be handled by
            # the skill manager when loading
        
        return True
    
    # ─────────────────────────────────────────────────────────
    # Data Access
    # ─────────────────────────────────────────────────────────
    
    def get_skills_dirs(self) -> Dict[str, Path]:
        """Get all skills directories"""
        return {
            "builtin": self.skills_builtin,
            "user": self.skills_user,
        }
    
    def get_log_files(self) -> List[Path]:
        """Get all log files sorted by modification time (newest first)"""
        if not self.logs_dir.exists():
            return []
        return sorted(
            self.logs_dir.glob("conversation_*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get data store statistics"""
        log_files = self.get_log_files()
        total_entries = 0
        for f in log_files:
            try:
                with open(f) as fh:
                    total_entries += sum(1 for _ in fh if _.strip())
            except IOError:
                pass
        
        builtin_skills = 0
        if self.skills_builtin.exists():
            builtin_skills = len(list(self.skills_builtin.glob("*/SKILL.md")))
        
        user_skills = 0
        if self.skills_user.exists():
            user_skills = len(list(self.skills_user.glob("*/SKILL.md")))
        
        return {
            "version": str(self.get_version()),
            "pending_migrations": len(self.get_pending_migrations()),
            "logs": {
                "files": len(log_files),
                "entries": total_entries,
            },
            "skills": {
                "builtin": builtin_skills,
                "user": user_skills,
            },
        }
    
    def is_legacy(self) -> bool:
        """Check if this is a legacy installation (before user/system separation)"""
        return not self.version_file.exists()
    
    def is_migration_needed(self) -> bool:
        """Check if any migration is pending"""
        return len(self.get_pending_migrations()) > 0


# ─────────────────────────────────────────────────────────────────
# Global Singleton
# ─────────────────────────────────────────────────────────────────

_instance: Optional[DataStore] = None


def get_data_store() -> DataStore:
    """Get the global DataStore instance"""
    global _instance
    if _instance is None:
        _instance = DataStore()
    return _instance


def init_data_store() -> DataStore:
    """Initialize data store and run pending migrations"""
    store = get_data_store()
    
    # Run migrations
    if not store.migrate():
        logger.error("data_migration_failed")
        raise RuntimeError("Data migration failed. Please check logs.")
    
    return store
