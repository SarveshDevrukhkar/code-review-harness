from code_review_harness.passes.base import ReviewPass, load_prompt
from code_review_harness.passes.unified import JSON_SCHEMA_HINT


class BestPracticesReviewPass(ReviewPass):
    name = "best_practices"
    category = "best_practice"

    def system_prompt(self) -> str:
        base = load_prompt(
            "best_practices",
            "You enforce language and framework best practices: idiomatic patterns, project "
            "structure, dependency usage, logging, configuration, and documentation gaps.",
        )
        return base + "\n\n" + JSON_SCHEMA_HINT.replace(
            '"category": "security|bug|quality|best_practice"',
            '"category": "best_practice"',
        )