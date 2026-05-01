"""Component 6: Runner / Evaluator — orchestrates task execution and result collection."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .task import Task, TaskResult
from .adapter import ModelAdapter
from .prompting import get_strategy
from .metrics import get_scorer
from .loader import get_benchmark_registry


class Runner:
    """Executes tasks through the adapter and collects results."""

    def __init__(
        self,
        adapter: ModelAdapter,
        max_workers: int = 4,
        timeout_per_task: int = 120,
    ):
        self.adapter = adapter
        self.max_workers = max_workers
        self.timeout = timeout_per_task

    def run_task(self, task: Task) -> TaskResult:
        """Run a single task and return the result."""
        start = time.time()
        try:
            # Build prompt using strategy
            strategy = get_strategy(task.task_type)
            system_prompt, user_prompt = strategy.build(task.prompt)

            # Generate via adapter
            full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
            prediction = self.adapter.generate(full_prompt)

            # Score
            scorer = get_scorer(task.task_type)
            score, metric_details = scorer.score(prediction, task.reference)

            duration_ms = (time.time() - start) * 1000
            return TaskResult(
                task_id=task.id,
                success=True,
                prediction=prediction,
                score=score,
                metrics=metric_details,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return TaskResult(
                task_id=task.id,
                success=False,
                prediction="",
                score=0.0,
                error=str(e),
                duration_ms=duration_ms,
            )

    def run_benchmark(self, benchmark_name: str) -> list[TaskResult]:
        """Run all tasks in a benchmark."""
        registry = get_benchmark_registry()
        benchmark = registry.get(benchmark_name)
        if not benchmark:
            raise ValueError(f"Benchmark '{benchmark_name}' not found")

        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.run_task, task): task for task in benchmark.tasks}
            for future in as_completed(futures):
                results.append(future.result())

        return results

    def summarize_results(self, results: list[TaskResult]) -> dict[str, Any]:
        """Aggregate results into a summary dict."""
        total = len(results)
        passed = sum(1 for r in results if r.success)
        avg_score = sum(r.score for r in results) / total if total else 0.0
        avg_duration = sum(r.duration_ms for r in results) / total if total else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total else 0.0,
            "avg_score": avg_score,
            "avg_duration_ms": avg_duration,
            "results": results,
        }
