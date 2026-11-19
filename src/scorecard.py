
from datetime import timedelta, time

from metrics import (
    calculate_lsr,
    calculate_scr,
    calculate_return_rate,
    calculate_rating,
    calculate_response_time,
)


def time_in_window(ts):
    return time(9, 0) <= ts.time() <= time(21, 0)


def build_scorecard(
    seller_id,
    review_week,
    all_orders,
    all_messages,
    review_date=None
):
    """
    Calculate seller metrics using event dates.

    Windows exclude the current review date.
    """

    orders = [
        o for o in all_orders
        if o["seller_id"] == seller_id
    ]

    messages = [
        m for m in all_messages
        if m["seller_id"] == seller_id
    ]

    if review_date is None:
        # Compatibility with older callers.
        four = [
            o for o in orders
            if max(1, review_week - 3)
            <= o["week_no"] <= review_week
        ]

        eight = [
            o for o in orders
            if max(1, review_week - 7)
            <= o["week_no"] <= review_week
        ]

        shipped = [
            o for o in four
            if o.get("shipped_ts") is not None
        ]

        cancelled = [
            o for o in four
            if o.get("cancelled_ts") is not None
        ]

        delivered = [
            o for o in eight
            if o.get("delivered_ts") is not None
        ]

        rating_orders = eight

        weekly_messages = [
            m for m in messages
            if m.get("week_no") == review_week
        ]

        scr_denominator = len(four)

    else:
        start4 = review_date - timedelta(weeks=4)
        start8 = review_date - timedelta(weeks=8)
        start1 = review_date - timedelta(weeks=1)

        def in_window(ts, start):
            return (
                ts is not None
                and start <= ts.date() < review_date
            )

        shipped = [
            o for o in orders
            if in_window(o.get("shipped_ts"), start4)
        ]

        cancelled = [
            o for o in orders
            if in_window(o.get("cancelled_ts"), start4)
        ]

        placed = [
            o for o in orders
            if in_window(o.get("order_ts"), start4)
        ]

        delivered = [
            o for o in orders
            if in_window(o.get("delivered_ts"), start8)
        ]

        # The dataset has no separate rating timestamp.
        # Delivery date is used as a proxy.
        rating_orders = delivered

        weekly_messages = [
            m for m in messages
            if in_window(m.get("msg_ts"), start1)
        ]

        scr_denominator = len(placed)

    rating_count = sum(
        o.get("rating") is not None
        for o in rating_orders
    )

    response = calculate_response_time(weekly_messages)

    unanswered = sum(
        m.get("reply_ts") is None
        for m in weekly_messages
        if (
            m.get("msg_ts") is not None
            and time_in_window(m["msg_ts"])
        )
    )

    return {
        "seller_id": seller_id,
        "review_week": review_week,
        "shipped_count": len(shipped),
        "lsr": (
            calculate_lsr(shipped)
            if len(shipped) >= 20
            else None
        ),
        "scr": calculate_scr(
            cancelled,
            denominator=scr_denominator
        ),
        "return_rate": calculate_return_rate(delivered),
        "rating": calculate_rating(rating_orders),
        "rating_count": rating_count,
        "response_hours": response,
        "unanswered_messages": unanswered,
    }
