"""Component 1: Task / Benchmark Definition."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """Single evaluation task definition."""
    id: str
    name: str
    task_type: str  # "code_generation" | "bug_fix" | "code_review" | "architecture"
    prompt: str
    reference: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of running a single task."""
    task_id: str
    success: bool
    prediction: str
    score: float
    metrics: dict = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class Benchmark:
    """Collection of tasks forming a benchmark suite."""
    name: str
    description: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> "Benchmark":
        self.tasks.append(task)
        return self

    def __len__(self) -> int:
        return len(self.tasks)

    def get_task(self, task_id: str) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None
