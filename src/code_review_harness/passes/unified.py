from code_review_harness.passes.base import ReviewPass, load_prompt

JSON_SCHEMA_HINT = """
Respond with JSON object:
{
  "chunk_summary": "one sentence",
  "findings": [
    {
      "category": "security|bug|quality|best_practice",
      "severity": "critical|high|medium|low|info",
      "file": "path from header",
      "line_start": 1,
      "line_end": 1,
      "title": "short title",
      "description": "what is wrong and why",
      "recommendation": "concrete fix"
    }
  ]
}
Only report real issues supported by the shown lines. Use empty findings if none.
"""


class UnifiedReviewPass(ReviewPass):
    name = "unified"
    category = "quality"  # default when parsing omits category

    def system_prompt(self) -> str:
        base = load_prompt(
            "unified",
            "You are an expert code reviewer. Analyze code for security vulnerabilities, "
            "bugs, code quality, and engineering best practices. Be precise and cite line numbers.",
        )
        return base + "\n\n" + JSON_SCHEMA_HINT