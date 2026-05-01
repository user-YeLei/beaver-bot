"""BeaverHarness — orchestrates all 6 components into a unified evaluation API."""

from typing import Any, Optional

from .task import Task, Benchmark, TaskResult
from .adapter import ModelAdapter, BeaverAdapter
from .runner import Runner
from .loader import (
    BenchmarkRegistry,
    get_benchmark_registry,
    register_benchmark,
    list_benchmarks,
)


class BeaverHarness:
    """Unified evaluation harness combining all 6 components:

    1. Task/Benchmark Definition — Task, Benchmark, TaskResult
    2. Model Adapter            — ModelAdapter (BeaverAdapter, OpenAIAdapter, ...)
    3. Prompting Strategy       — PromptStrategy per task type
    4. Scoring/Metrics         — Scorer subclasses + get_scorer()
    5. Data Loader             — TaskLoader + BenchmarkRegistry
    6. Runner/Evaluator        — Runner.run_benchmark() + summarize_results()
    """

    def __init__(
        self,
        adapter: ModelAdapter,
        max_workers: int = 4,
        benchmark_dir: Optional[str] = None,
    ):
        self.adapter = adapter
        self.runner = Runner(adapter, max_workers=max_workers)
        self.registry = get_benchmark_registry()

        if benchmark_dir:
            self.registry.load_from_directory(benchmark_dir)

    def add_task(self, task: Task) -> "BeaverHarness":
        """Add a single task to an in-memory ephemeral benchmark."""
        if "ephemeral" not in self.registry.list_benchmarks():
            self.registry.register(Benchmark(name="ephemeral"))
        self.registry.get("ephemeral").add_task(task)
        return self

    def load_benchmarks(self, dir_path: str) -> "BeaverHarness":
        """Load all .json benchmarks from a directory."""
        self.registry.load_from_directory(dir_path)
        return self

    def register_benchmark(self, benchmark: Benchmark) -> "BeaverHarness":
        self.registry.register(benchmark)
        return self

    def run(
        self,
        benchmark_name: str,
        summarize: bool = True,
    ) -> dict[str, Any] | list[TaskResult]:
        """Run a named benchmark and optionally summarize results."""
        results = self.runner.run_benchmark(benchmark_name)
        if summarize:
            return self.runner.summarize_results(results)
        return results

    def run_single(self, task: Task) -> TaskResult:
        """Run one task immediately."""
        return self.runner.run_task(task)

    def list_benchmarks(self) -> list[str]:
        return self.registry.list_benchmarks()

    def benchmark_info(self, name: str) -> dict[str, Any]:
        bm = self.registry.get(name)
        if not bm:
            return {}
        return {
            "name": bm.name,
            "description": bm.description,
            "task_count": len(bm.tasks),
            "task_types": list(set(t.task_type for t in bm.tasks)),
        }
