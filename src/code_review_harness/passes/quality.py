from code_review_harness.passes.base import ReviewPass, load_prompt
from code_review_harness.passes.unified import JSON_SCHEMA_HINT


class QualityReviewPass(ReviewPass):
    name = "quality"
    category = "quality"

    def system_prompt(self) -> str:
        base = load_prompt(
            "quality",
            "You review code quality: complexity, readability, naming, duplication smells, "
            "missing tests for critical paths, and maintainability risks.",
        )
        return base + "\n\n" + JSON_SCHEMA_HINT.replace(
            '"category": "security|bug|quality|best_practice"',
            '"category": "quality"',
        )