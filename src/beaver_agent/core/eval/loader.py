"""Component 5: Data Loader — loading and parsing benchmark datasets."""

import json
from pathlib import Path
from typing import Iterator

from .task import Task, Benchmark


class TaskLoader:
    """Loads tasks from various sources (JSON, YAML, Python dict)."""

    @staticmethod
    def from_json_file(path: str) -> list[Task]:
        """Load tasks from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        return [Task(**item) for item in data.get("tasks", [])]

    @staticmethod
    def from_dict_list(tasks_data: list[dict]) -> list[Task]:
        """Load tasks from a list of dictionaries."""
        return [Task(**td) for td in tasks_data]

    @staticmethod
    def from_harness_format(file_path: str) -> Benchmark:
        """Load a complete benchmark from a single JSON file."""
        with open(file_path) as f:
            data = json.load(f)
        benchmark = Benchmark(
            name=data.get("name", "benchmark"),
            description=data.get("description", ""),
        )
        for td in data.get("tasks", []):
            benchmark.add_task(Task(**td))
        return benchmark


class BenchmarkRegistry:
    """Discovers and registers built-in + custom benchmarks."""

    def __init__(self):
        self._benchmarks: dict[str, Benchmark] = {}

    def register(self, benchmark: Benchmark) -> "BenchmarkRegistry":
        self._benchmarks[benchmark.name] = benchmark
        return self

    def get(self, name: str) -> Benchmark | None:
        return self._benchmarks.get(name)

    def list_benchmarks(self) -> list[str]:
        return list(self._benchmarks.keys())

    def load_from_directory(self, dir_path: str) -> "BenchmarkRegistry":
        """Load all .json benchmark files from a directory."""
        p = Path(dir_path)
        for fp in p.glob("*.json"):
            try:
                bm = TaskLoader.from_harness_format(str(fp))
                self.register(bm)
            except Exception:
                pass  # skip invalid files
        return self


# Global registry
_benchmark_registry = BenchmarkRegistry()


def get_benchmark_registry() -> BenchmarkRegistry:
    return _benchmark_registry


def register_benchmark(benchmark: Benchmark):
    _benchmark_registry.register(benchmark)


def list_benchmarks() -> list[str]:
    return _benchmark_registry.list_benchmarks()
