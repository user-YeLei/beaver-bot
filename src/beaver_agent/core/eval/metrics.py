"""Component 4: Scoring / Metrics — how to evaluate predictions."""

from abc import ABC, abstractmethod
import difflib
import re
from typing import Any


class Scorer(ABC):
    """Base class for all scoring strategies."""

    @abstractmethod
    def score(self, prediction: str, reference: str, context: dict = None) -> tuple[float, dict]:
        """
        Returns (score, details_dict).
        Score is 0.0-1.0 for most scorers.
        """
        raise NotImplementedError


class ExactMatchScorer(Scorer):
    """Binary exact match - 1.0 if identical, 0.0 otherwise."""

    def score(self, prediction: str, reference: str, context: dict = None) -> tuple[float, dict]:
        match = prediction.strip() == reference.strip()
        return (1.0 if match else 0.0), {"exact_match": match}


class SimilarityScorer(Scorer):
    """Levenshtein-based string similarity."""

    def score(self, prediction: str, reference: str, context: dict = None) -> tuple[float, dict]:
        ratio = difflib.SequenceMatcher(None, prediction.strip(), reference.strip()).ratio()
        return ratio, {"similarity": ratio}


class CodeExecutionScorer(Scorer):
    """Execute generated code and check if it passes test cases."""

    def __init__(self, test_cases: list[dict]):
        # test_cases: [{"input": ..., "expected": ...}]
        self.test_cases = test_cases

    def score(self, prediction: str, reference: str, context: dict = None) -> tuple[float, dict]:
        passed = 0
        errors = []
        for tc in self.test_cases:
            try:
                local_vars = {}
                exec(prediction, {}, local_vars)
                result = local_vars.get("result", None)
                if str(result) == str(tc.get("expected", "")):
                    passed += 1
            except Exception as e:
                errors.append(str(e))
        score = passed / len(self.test_cases) if self.test_cases else 0.0
        return score, {"passed": passed, "total": len(self.test_cases), "errors": errors}


class CodeReviewScorer(Scorer):
    """Score code review quality by checking for key elements."""

    def score(self, prediction: str, reference: str, context: dict = None) -> tuple[float, dict]:
        keywords = ["bug", "security", "performance", "readability", "issue", "recommend"]
        found = sum(1 for kw in keywords if kw.lower() in prediction.lower())
        coverage = found / len(keywords)
        return coverage, {"keyword_coverage": coverage, "keywords_found": found}


def get_scorer(task_type: str) -> Scorer:
    return {
        "code_generation": SimilarityScorer(),
        "bug_fix": ExactMatchScorer(),
        "code_review": CodeReviewScorer(),
        "architecture": SimilarityScorer(),
    }.get(task_type, SimilarityScorer())
