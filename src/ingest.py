from datetime import datetime
from loaders import load_csv


def parse_ts(text):
    """Turn '2026-08-09 21:02:36' into a date-time. Empty text gives None."""
    text = text.strip()
    if text == "":
        return None
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")


def parse_date(text):
    """Turn '2026-08-07' into a date. Empty text gives None."""
    text = text.strip()
    if text == "":
        return None
    return datetime.strptime(text, "%Y-%m-%d").date()


def load_orders(path, week_no, seen_ids):
    """Read one orders file. Returns (good_orders, rejected_list).
    seen_ids remembers every order_id already loaded, to skip duplicates."""
    good = []
    rejected = []
    for row in load_csv(path):
        order_id = row["order_id"].strip()

        # Duplicate row: process only once
        if order_id in seen_ids:
            continue

        order = {
            "order_id": order_id,
            "seller_id": row["seller_id"].strip(),
            "week_no": week_no,
            "order_ts": parse_ts(row["order_ts"]),
            "gmv": float(row["gmv"]),
            "prepaid": row["prepaid"].strip().lower() == "true",
            "promised": parse_date(row["promised_ship_date"]),
            "shipped_ts": parse_ts(row["shipped_ts"]),
            "cancelled_ts": parse_ts(row["cancelled_ts"]),
            "cancelled_by": row["cancelled_by"].strip(),
            "cancel_reason": row["cancel_reason"].strip(),
            "delivered_ts": parse_ts(row["delivered_ts"]),
            "return_reason": row["return_reason"].strip(),
            "rating": None,
        }

        # Rating: keep only 1 to 5 (the planted 6 is ignored, the order is kept)
        rating_text = row["rating"].strip()
        if rating_text != "":
            rating = int(rating_text)
            if 1 <= rating <= 5:
                order["rating"] = rating

        # Shipped before it was ordered: reject the whole row
        if order["shipped_ts"] is not None and order["shipped_ts"] < order["order_ts"]:
            rejected.append((order_id, "INVALID_SEQUENCE"))
            continue

        seen_ids.add(order_id)
        good.append(order)
    return good, rejected


def load_messages(path):
    """Read one messages file. Returns a list of message dictionaries."""
    messages = []
    for row in load_csv(path):
        messages.append({
            "message_id": row["message_id"].strip(),
            "order_id": row["order_id"].strip(),
            "seller_id": row["seller_id"].strip(),
            "msg_ts": parse_ts(row["buyer_msg_ts"]),
            "reply_ts": parse_ts(row["seller_reply_ts"]),
        })
    return messages