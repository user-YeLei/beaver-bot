"""Beaver Bot Skill Manager - Structured skill loading and execution"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class SkillStep:
    """A single step in a skill phase"""
    order: int
    instruction: str
    check: Optional[str] = None  # What to verify after this step


@dataclass
class SkillPhase:
    """A phase in a skill (e.g., Requirements, Implementation, Review)"""
    name: str
    instruction: str
    steps: List[SkillStep] = field(default_factory=list)


@dataclass
class Skill:
    """Represents a loaded skill"""

    name: str
    category: str
    description: str
    trigger: str
    content: str
    file_path: Path
    required_commands: List[str] = field(default_factory=list)
    required_environment_variables: List[str] = field(default_factory=list)

    # New structured fields (Matt Pocock style)
    when_to_use: str = ""           # When to invoke this skill
    phases: List[SkillPhase] = field(default_factory=list)
    checklist: List[str] = field(default_factory=list)  # Final verification checklist
    examples: List[str] = field(default_factory=list)     # Usage examples

    # Backward compatibility: if no phases, use the whole content as one phase
    @property
    def is_structured(self) -> bool:
        return len(self.phases) > 0

    def matches(self, user_input: str) -> bool:
        """Check if user input matches this skill's trigger"""
        if not self.trigger:
            return False
        trigger_lower = self.trigger.lower()
        input_lower = user_input.lower()
        return trigger_lower in input_lower

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "trigger": self.trigger,
            "when_to_use": self.when_to_use,
            "phases": [
                {
                    "name": p.name,
                    "instruction": p.instruction,
                    "steps": [{"order": s.order, "instruction": s.instruction, "check": s.check}
                              for s in p.steps]
                }
                for p in self.phases
            ],
            "checklist": self.checklist,
            "examples": self.examples,
            "file_path": str(self.file_path),
        }

    def get_prompt(self) -> str:
        """Get the full skill content as a prompt for the agent"""
        if self.is_structured:
            lines = [f"# {self.name}\n"]
            if self.when_to_use:
                lines.append(f"**When to use**: {self.when_to_use}\n")
            lines.append(f"\n{self.description}\n")

            for phase in self.phases:
                lines.append(f"\n## {phase.name}\n")
                if phase.instruction:
                    lines.append(f"{phase.instruction}\n")
                for step in phase.steps:
                    lines.append(f"{step.order}. {step.instruction}")
                    if step.check:
                        lines.append(f"   - Verify: {step.check}")

            if self.checklist:
                lines.append("\n## Verification Checklist\n")
                for item in self.checklist:
                    lines.append(f"- [ ] {item}")

            if self.examples:
                lines.append("\n## Examples\n")
                for ex in self.examples:
                    lines.append(f"- {ex}")

            return "\n".join(lines)
        else:
            # Fallback: strip frontmatter and return content
            return self.content


class SkillManager:
    """
    Manages skill loading, discovery, and execution.
    
    Supports user/system skill separation:
    - data/skills/builtin/  → System skills (overwritten on upgrade)
    - data/skills/user/      → User skills (preserved on upgrade)
    
    User skills take priority over builtin skills with the same name.
    """

    SKILL_FILE = "SKILL.md"

    def __init__(self, project_root: Path, skills_dirs: Dict[str, Path] = None):
        self.project_root = project_root
        self._skills: Dict[str, Skill] = {}
        
        # Default: check new data/ location, fall back to legacy skills/
        if skills_dirs:
            self.skills_dirs = skills_dirs
        else:
            data_dir = project_root / "data"
            self.skills_dirs = {
                "builtin": data_dir / "skills" / "builtin",
                "user": data_dir / "skills" / "user",
            }
        
        self._load_skills()

    def _load_skills(self) -> None:
        """Discover and load all skills from skills directories.
        
        Loads in order: builtin first, then user.
        User skills with same name override builtin skills.
        """
        loaded = set()
        
        # Load builtin skills first
        builtin_dir = self.skills_dirs.get("builtin")
        if builtin_dir and builtin_dir.exists():
            for skill_path in builtin_dir.rglob(self.SKILL_FILE):
                skill = self._parse_skill_file(skill_path)
                if skill:
                    self._skills[skill.name] = skill
                    loaded.add(skill.name)
                    logger.info("skill_loaded", name=skill.name, 
                               source="builtin", structured=skill.is_structured)
        
        # Load user skills (can override builtin)
        user_dir = self.skills_dirs.get("user")
        if user_dir and user_dir.exists():
            for skill_path in user_dir.rglob(self.SKILL_FILE):
                skill = self._parse_skill_file(skill_path)
                if skill:
                    # User skill overrides builtin if same name
                    is_override = skill.name in loaded
                    self._skills[skill.name] = skill
                    loaded.add(skill.name)
                    logger.info("skill_loaded", name=skill.name,
                               source="user" if is_override else "user_new",
                               structured=skill.is_structured)
        
        # Also check legacy skills/ directory for backward compatibility
        legacy_dir = self.project_root / "skills"
        if legacy_dir.exists():
            for skill_path in legacy_dir.rglob(self.SKILL_FILE):
                skill = self._parse_skill_file(skill_path)
                if skill and skill.name not in loaded:
                    self._skills[skill.name] = skill
                    loaded.add(skill.name)
                    logger.info("skill_loaded", name=skill.name,
                               source="legacy", structured=skill.is_structured)

        logger.info("skills_loaded_total", count=len(self._skills))

    def _parse_skill_file(self, file_path: Path) -> Optional[Skill]:
        """Parse a SKILL.md file and extract metadata and structured content"""
        try:
            content = file_path.read_text(encoding="utf-8")
            frontmatter = self._extract_frontmatter(content)

            name = frontmatter.get("name", file_path.parent.name)
            category = frontmatter.get("category", "general")
            description = frontmatter.get("description", "")
            trigger = frontmatter.get("trigger", "")
            required_commands = frontmatter.get("required_commands", [])
            required_env_vars = frontmatter.get("required_environment_variables", [])
            when_to_use = frontmatter.get("when_to_use", "")
            checklist = frontmatter.get("checklist", [])
            examples = frontmatter.get("examples", [])

            # Parse structured phases if present
            phases = self._parse_phases(frontmatter)

            return Skill(
                name=name,
                category=category,
                description=description,
                trigger=trigger,
                content=content,
                file_path=file_path,
                required_commands=required_commands,
                required_environment_variables=required_env_vars,
                when_to_use=when_to_use,
                phases=phases,
                checklist=checklist,
                examples=examples,
            )
        except Exception as e:
            logger.error("skill_parse_failed", file=str(file_path), error=str(e))
            return None

    def _parse_phases(self, frontmatter: Dict[str, Any]) -> List[SkillPhase]:
        """Parse structured phases from frontmatter"""
        phases = []
        raw_phases = frontmatter.get("phases", [])

        if not raw_phases:
            # Try legacy format: steps as a list
            raw_steps = frontmatter.get("steps", [])
            if raw_steps and isinstance(raw_steps, list):
                steps = []
                for i, step_text in enumerate(raw_steps, 1):
                    if isinstance(step_text, dict):
                        steps.append(SkillStep(
                            order=i,
                            instruction=step_text.get("instruction", str(step_text)),
                            check=step_text.get("check")
                        ))
                    else:
                        steps.append(SkillStep(order=i, instruction=str(step_text)))
                phases.append(SkillPhase(name="Steps", instruction="", steps=steps))

            # Try new format: phases as list of {name, instruction, steps}
            raw_phases = frontmatter.get("phases", [])

        for phase_data in raw_phases:
            if isinstance(phase_data, dict):
                phase_name = phase_data.get("name", "Unnamed")
                phase_instruction = phase_data.get("instruction", "")
                raw_steps = phase_data.get("steps", [])

                steps = []
                for i, step_text in enumerate(raw_steps, 1):
                    if isinstance(step_text, dict):
                        steps.append(SkillStep(
                            order=i,
                            instruction=step_text.get("instruction", str(step_text)),
                            check=step_text.get("check")
                        ))
                    elif isinstance(step_text, str):
                        steps.append(SkillStep(order=i, instruction=step_text))
                    else:
                        steps.append(SkillStep(order=i, instruction=str(step_text)))

                phases.append(SkillPhase(
                    name=phase_name,
                    instruction=phase_instruction,
                    steps=steps
                ))

        return phases

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from skill content"""
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as e:
                logger.warning("yaml_parse_failed", error=str(e))
        return {}

    def find_matching_skill(self, user_input: str) -> Optional[Skill]:
        """Find the first skill that matches the user input"""
        for skill in self._skills.values():
            if skill.matches(user_input):
                logger.debug("skill_matched", skill=skill.name, trigger=skill.trigger)
                return skill
        return None

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self._skills.get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills"""
        return [skill.to_dict() for skill in self._skills.values()]

    def list_skills_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List skills in a specific category"""
        return [
            skill.to_dict() for skill in self._skills.values()
            if skill.category == category
        ]

    def reload(self) -> None:
        """Reload all skills from disk"""
        self._skills.clear()
        self._load_skills()
