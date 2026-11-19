
from metrics import is_late


EXCLUDED_CANCELLATION_REASONS = {
    "BUYER_REQUEST",
    "ADDRESS_UNSERVICEABLE"
}


def calculate_weekly_penalties(orders):
    """Calculate ordinary weekly penalties for one seller."""

    late_orders = [
        order for order in orders
        if order["shipped_ts"] is not None
        and is_late(order["promised"], order["shipped_ts"])
    ]

    # First 3 late shipments per week are penalty-free
    chargeable_late = max(0, len(late_orders) - 3)
    late_penalty = chargeable_late * 50

    cancellation_penalty = 0

    for order in orders:
        if (
            order["cancelled_by"] == "SELLER"
            and order["cancel_reason"]
            not in EXCLUDED_CANCELLATION_REASONS
        ):
            cancellation_penalty += (
                200 if order["prepaid"] else 100
            )

    weekly_gmv = sum(order["gmv"] for order in orders)

    uncapped_total = late_penalty + cancellation_penalty

    weekly_cap = min(5000, weekly_gmv * 0.05)

    final_penalty = min(uncapped_total, weekly_cap)

    return {
        "late_orders": len(late_orders),
        "chargeable_late": chargeable_late,
        "late_penalty": late_penalty,
        "cancellation_penalty": cancellation_penalty,
        "weekly_gmv": round(weekly_gmv, 2),
        "weekly_cap": round(weekly_cap, 2),
        "uncapped_total": uncapped_total,
        "final_penalty": round(final_penalty, 2)
    }


def create_penalty_entries(orders, week_no):
    """Create order-level penalty records before weekly cap."""

    entries = []

    late_orders = [
        order for order in orders
        if order["shipped_ts"] is not None
        and is_late(order["promised"], order["shipped_ts"])
    ]

    # Sort so the first three late shipments are exempt
    late_orders.sort(
        key=lambda order: (
            order["shipped_ts"],
            order["order_id"]
        )
    )

    for order in late_orders[3:]:
        entries.append({
            "seller_id": order["seller_id"],
            "order_id": order["order_id"],
            "week_no": week_no,
            "reason": "LATE_SHIPMENT",
            "amount": 50.0
        })

    for order in orders:
        if (
            order["cancelled_by"] == "SELLER"
            and order["cancel_reason"]
            not in EXCLUDED_CANCELLATION_REASONS
        ):
            entries.append({
                "seller_id": order["seller_id"],
                "order_id": order["order_id"],
                "week_no": week_no,
                "reason": "SELLER_CANCELLATION",
                "amount": 200.0 if order["prepaid"] else 100.0
            })

    return entries


def apply_weekly_cap(entries, weekly_gmv):
    """Apply the weekly cap to ordinary penalty entries."""

    total_penalty = sum(
        entry["amount"] for entry in entries
    )

    cap = min(5000.0, weekly_gmv * 0.05)

    final_penalty = min(total_penalty, cap)

    return {
        "total_penalty": round(total_penalty, 2),
        "weekly_cap": round(cap, 2),
        "final_penalty": round(final_penalty, 2),
        "cap_reduction": round(total_penalty - final_penalty, 2)
    }


