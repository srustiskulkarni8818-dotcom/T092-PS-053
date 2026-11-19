
import sys
from pathlib import Path
from datetime import datetime, date

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from metrics import (
    is_late,
    calculate_lsr,
    calculate_scr,
    calculate_return_rate,
    calculate_rating,
    calculate_response_time,
)
from tiers import apply_tier_review


def make_order(**changes):
    order = {
        "promised": date(2026, 8, 7),
        "shipped_ts": None,
        "cancelled_ts": None,
        "cancelled_by": "",
        "cancel_reason": "",
        "delivered_ts": None,
        "return_reason": "",
        "rating": None,
    }
    order.update(changes)
    return order


def test_friday_weekend_grace():
    shipped = datetime(2026, 8, 8, 23, 59, 59)
    assert is_late(date(2026, 8, 7), shipped) is False


def test_one_second_after_grace():
    shipped = datetime(2026, 8, 9, 0, 0, 0)
    assert is_late(date(2026, 8, 7), shipped) is True


def test_lsr_percentage():
    orders = [
        make_order(
            shipped_ts=datetime(2026, 8, 7, 12)
        )
        for _ in range(19)
    ]

    orders.append(
        make_order(
            shipped_ts=datetime(2026, 8, 9, 12)
        )
    )

    assert calculate_lsr(orders) == 5.0


def test_scr_exact_boundary():
    orders = [make_order() for _ in range(200)]

    for order in orders[:5]:
        order["cancelled_ts"] = datetime(2026, 8, 10)
        order["cancelled_by"] = "SELLER"
        order["cancel_reason"] = "OUT_OF_STOCK"

    assert calculate_scr(orders) == 2.5


def test_excluded_cancellation():
    orders = [
        make_order(
            cancelled_ts=datetime(2026, 8, 10),
            cancelled_by="SELLER",
            cancel_reason="BUYER_REQUEST"
        )
    ]

    assert calculate_scr(orders) == 0.0


def test_fashion_return_boundary():
    orders = [
        make_order(
            delivered_ts=datetime(2026, 8, 10)
        )
        for _ in range(300)
    ]

    for order in orders[:30]:
        order["return_reason"] = "DEFECTIVE"

    assert calculate_return_rate(orders) == 10.0


def test_rating_minimum():
    orders = [
        make_order(rating=5)
        for _ in range(9)
    ]

    assert calculate_rating(orders) is None

    orders.append(make_order(rating=5))
    assert calculate_rating(orders) == 5.0


def test_response_time_boundary():
    messages = [
        {
            "msg_ts": datetime(2026, 8, 10, 21, 0),
            "reply_ts": datetime(2026, 8, 11, 9, 0),
        },
        {
            "msg_ts": datetime(2026, 8, 10, 21, 0, 1),
            "reply_ts": datetime(2026, 8, 11, 9, 0),
        },
    ]

    assert calculate_response_time(messages) == 12.0


def test_unanswered_message():
    messages = [
        {
            "msg_ts": datetime(2026, 8, 10, 10),
            "reply_ts": None,
        }
    ]

    assert calculate_response_time(messages) > 24


def test_tier_upgrade_one_step():
    assert apply_tier_review(
        "WATCH", "PLATINUM"
    ) == "SILVER"

    assert apply_tier_review(
        "SILVER", "PLATINUM"
    ) == "GOLD"

    assert apply_tier_review(
        "GOLD", "PLATINUM"
    ) == "PLATINUM"


def test_tier_downgrade():
    assert apply_tier_review(
        "PLATINUM", "WATCH"
    ) == "WATCH"

def test_sel025_week6_penalty_example():
    """
    Assignment example:
    80 shipments, 70 late before weekend grace.
    3 shipments receive weekend grace.
    First 3 late shipments are free.
    Weekly GMV is Rs 60,000.
    """
    total_shipments = 80
    late_before_grace = 70
    weekend_grace = 3
    free_late_shipments = 3
    penalty_per_late = 50
    weekly_gmv = 60000

    late_after_grace = late_before_grace - weekend_grace
    chargeable = max(
        0, late_after_grace - free_late_shipments
    )

    penalty_before_cap = chargeable * penalty_per_late
    weekly_cap = min(5000, weekly_gmv * 0.05)
    final_penalty = min(penalty_before_cap, weekly_cap)

    assert total_shipments == 80
    assert late_after_grace == 67
    assert penalty_before_cap == 3200
    assert final_penalty == 3000


def test_penalty_ledger_integrity():
    import csv
    from decimal import Decimal

    path = (
        Path(__file__).resolve().parents[1]
        / "output"
        / "penalty_ledger.csv"
    )

    assert path.exists(), "Run python src/main.py first"

    with path.open(newline="", encoding="utf-8") as file:
        penalties = list(csv.DictReader(file))

    assert penalties, "Penalty ledger is empty"

    for penalty in penalties:
        amount = Decimal(penalty["amount"])
        charged = Decimal(penalty["amount_after_cap"])

        assert amount >= 0
        assert charged >= 0

        if penalty["penalty_type"] == "COUNTERFEIT":
            assert amount == Decimal("25000.00")
            assert charged == Decimal("25000.00")
        else:
            assert charged <= amount

    ids = [p["penalty_id"] for p in penalties]
    assert len(ids) == len(set(ids))


def test_final_output_structure():
    import csv
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    output = root / "output"

    expected = {
        "scorecards.csv": [
            "seller_id", "week_no", "review_date",
            "shipped_4w", "lsr_pct", "lsr_evaluated",
            "scr_pct", "return_rate_pct",
            "median_response_hours", "avg_rating",
            "rating_count", "breaches", "tier",
            "commission_adj_pp", "search_boost",
            "state", "week_gmv", "week_penalty_levied"
        ],
        "penalty_ledger.csv": [
            "penalty_id", "seller_id", "week_no",
            "order_id", "penalty_type", "amount",
            "amount_after_cap", "status",
            "appeal_id", "reversal_date"
        ],
        "state_transitions.csv": [
            "seller_id", "transition_date",
            "from_state", "to_state", "trigger"
        ]
    }

    for filename, columns in expected.items():
        path = output / filename

        assert path.exists(), f"Missing: {filename}"

        with path.open(
            newline="", encoding="utf-8"
        ) as file:
            reader = csv.DictReader(file)
            assert reader.fieldnames == columns, (
                f"Incorrect columns in {filename}"
            )
            rows = list(reader)

        assert rows, f"{filename} is empty"

        if filename == "scorecards.csv":
            assert len(rows) == 360, (
                f"Expected 360 scorecards, got {len(rows)}"
            )

            seller_weeks = {
                (r["seller_id"], r["week_no"])
                for r in rows
            }
            assert len(seller_weeks) == 360

            assert all(
                r["lsr_evaluated"] in {"true", "false"}
                for r in rows
            )



