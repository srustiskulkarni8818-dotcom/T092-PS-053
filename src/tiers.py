
TIER_ORDER = ["WATCH", "SILVER", "GOLD", "PLATINUM"]

TIER_EFFECTS = {
    "PLATINUM": {"commission_change": -2, "search_boost": 1.3},
    "GOLD": {"commission_change": -1, "search_boost": 1.1},
    "SILVER": {"commission_change": 0, "search_boost": 1.0},
    "WATCH": {"commission_change": 2, "search_boost": 0.7},
}


def assign_tier(scorecard, category="GENERAL", seller_age_weeks=8):
    """Determine the target tier from seller performance."""

    lsr = scorecard["lsr"]
    scr = scorecard["scr"]
    return_rate = scorecard["return_rate"]
    rating = scorecard["rating"]
    response = scorecard["response_hours"]

    return_limit = 10 if category.upper() == "FASHION" else 5

    breaches = 0

    if lsr is not None and lsr > 5:
        breaches += 1

    if scr > 2.5:
        breaches += 1

    if return_rate > return_limit:
        breaches += 1

    if rating is not None and rating < 3.8:
        breaches += 1

    if response is not None and response > 24:
        breaches += 1

    if breaches >= 2:
        tier = "WATCH"
    elif (
        breaches == 0
        and lsr is not None
        and rating is not None
        and lsr < 2
        and scr < 1
        and return_rate < 3
        and rating >= 4.5
    ):
        tier = "PLATINUM"
    elif (
        lsr is not None
        and rating is not None
        and lsr < 5
        and scr < 2.5
        and rating >= 4.2
    ):
        tier = "GOLD"
    else:
        tier = "SILVER"

    # Sellers younger than 8 weeks cannot reach PLATINUM
    if seller_age_weeks < 8 and tier == "PLATINUM":
        tier = "GOLD"

    return tier, breaches


def apply_tier_review(current_tier, target_tier):
    """Allow only one upward tier step per review."""

    current_index = TIER_ORDER.index(current_tier)
    target_index = TIER_ORDER.index(target_tier)

    if target_index > current_index:
        return TIER_ORDER[current_index + 1]

    return target_tier
