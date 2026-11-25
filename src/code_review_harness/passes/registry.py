from code_review_harness.passes.unified import UnifiedReviewPass
from code_review_harness.passes.security import SecurityReviewPass
from code_review_harness.passes.bugs import BugsReviewPass
from code_review_harness.passes.quality import QualityReviewPass
from code_review_harness.passes.best_practices import BestPracticesReviewPass
from code_review_harness.passes.base import ReviewPass

PASS_REGISTRY: dict[str, type[ReviewPass]] = {
    "unified": UnifiedReviewPass,
    "security": SecurityReviewPass,
    "bugs": BugsReviewPass,
    "quality": QualityReviewPass,
    "best_practices": BestPracticesReviewPass,
}

ALL_FOCUSED = ["security", "bugs", "quality", "best_practices"]


def resolve_passes(names: list[str] | None) -> list[ReviewPass]:
    if not names:
        return [UnifiedReviewPass()]
    out: list[ReviewPass] = []
    for n in names:
        key = n.strip().lower()
        if key == "all":
            return [PASS_REGISTRY[k]() for k in ALL_FOCUSED]
        if key not in PASS_REGISTRY:
            keys = ", ".join(PASS_REGISTRY) + ", all"
            raise ValueError(f"Unknown pass: {n}. Choose from: {keys}")
        out.append(PASS_REGISTRY[key]())
    return out or [UnifiedReviewPass()]