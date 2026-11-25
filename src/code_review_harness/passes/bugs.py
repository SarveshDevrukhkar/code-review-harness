from code_review_harness.passes.base import ReviewPass, load_prompt
from code_review_harness.passes.unified import JSON_SCHEMA_HINT


class BugsReviewPass(ReviewPass):
    name = "bugs"
    category = "bug"

    def system_prompt(self) -> str:
        base = load_prompt(
            "bugs",
            "You are a senior engineer hunting bugs: logic errors, off-by-one, null/undefined "
            "handling, race conditions, resource leaks, incorrect error handling, API misuse.",
        )
        return base + "\n\n" + JSON_SCHEMA_HINT.replace(
            '"category": "security|bug|quality|best_practice"',
            '"category": "bug"',
        )