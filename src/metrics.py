
from datetime import datetime, time, timedelta
from statistics import median

QUALIFYING_RETURNS = {
    "DEFECTIVE",
    "NOT_AS_DESCRIBED",
    "WRONG_ITEM"
}

EXCLUDED_CANCELLATIONS = {
    "BUYER_REQUEST",
    "ADDRESS_UNSERVICEABLE"
}


def is_late(promised_date, shipped_ts):
    """Apply the Friday weekend grace rule."""
    if promised_date is None or shipped_ts is None:
        return False

    deadline = datetime.combine(
        promised_date,
        time(23, 59, 59)
    )

    if promised_date.weekday() == 4:
        deadline += timedelta(hours=24)

    return shipped_ts > deadline


def calculate_lsr(orders):
    shipped = [
        o for o in orders
        if o.get("shipped_ts") is not None
    ]

    if not shipped:
        return 0.0

    late_count = sum(
        is_late(o.get("promised"), o["shipped_ts"])
        for o in shipped
    )

    return round(100 * late_count / len(shipped), 2)


def calculate_scr(orders, denominator=None):
    total = (
        len(orders)
        if denominator is None
        else denominator
    )

    if not total:
        return 0.0

    cancellations = sum(
        o.get("cancelled_ts") is not None
        and o.get("cancelled_by") == "SELLER"
        and o.get("cancel_reason")
        not in EXCLUDED_CANCELLATIONS
        for o in orders
    )

    return round(100 * cancellations / total, 2)


def calculate_return_rate(orders, denominator=None):
    delivered = [
        o for o in orders
        if o.get("delivered_ts") is not None
    ]

    total = (
        len(delivered)
        if denominator is None
        else denominator
    )

    if not total:
        return 0.0

    qualifying = sum(
        o.get("return_reason") in QUALIFYING_RETURNS
        for o in delivered
    )

    return round(100 * qualifying / total, 2)


def calculate_rating(orders):
    ratings = [
        o["rating"]
        for o in orders
        if o.get("rating") is not None
    ]

    if len(ratings) < 10:
        return None

    return round(sum(ratings) / len(ratings), 2)


def calculate_response_time(messages):
    """Calculate median response time for in-hours messages."""
    hours = []

    for msg in messages:
        start = msg.get("msg_ts")

        if (
            start is None
            or not time(9, 0) <= start.time() <= time(21, 0)
        ):
            continue

        reply = msg.get("reply_ts")

        if reply is None:
            hours.append(24.01)
        elif reply >= start:
            hours.append(
                (reply - start).total_seconds() / 3600
            )

    return round(median(hours), 2) if hours else None


def parse_date(value):
    return (
        datetime.strptime(value, "%Y-%m-%d").date()
        if value else None
    )


def parse_timestamp(value):
    return (
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        if value else None
    )
