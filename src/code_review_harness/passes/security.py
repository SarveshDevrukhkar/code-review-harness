from code_review_harness.passes.base import ReviewPass, load_prompt
from code_review_harness.passes.unified import JSON_SCHEMA_HINT


class SecurityReviewPass(ReviewPass):
    name = "security"
    category = "security"

    def system_prompt(self) -> str:
        base = load_prompt(
            "security",
            "You are a security-focused code reviewer. Find vulnerabilities: injection, "
            "broken auth, sensitive data exposure, misconfiguration, unsafe crypto, SSRF, "
            "path traversal, and hardcoded secrets.",
        )
        return base + "\n\n" + JSON_SCHEMA_HINT.replace(
            '"category": "security|bug|quality|best_practice"',
            '"category": "security"',
        )