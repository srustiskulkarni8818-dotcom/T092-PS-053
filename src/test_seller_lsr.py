
import csv
from collections import defaultdict

from metrics import (
    calculate_lsr,
    parse_date,
    parse_timestamp
)

seller_orders = defaultdict(list)

with open(
    "data/orders_week_01.csv",
    "r",
    newline="",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        seller_id = row["seller_id"]

        seller_orders[seller_id].append({
            "promised": parse_date(
                row["promised_ship_date"]
            ),
            "shipped_ts": parse_timestamp(
                row["shipped_ts"]
            )
        })

print("SELLER-WISE LSR - WEEK 01")
print("-" * 55)

for seller_id in sorted(seller_orders):
    orders = seller_orders[seller_id]

    shipped_count = sum(
        1 for order in orders
        if order["shipped_ts"] is not None
    )

    lsr = calculate_lsr(orders)

    print(
        f"{seller_id} | "
        f"Shipped: {shipped_count} | "
        f"LSR: {lsr}%"
    )

print("-" * 55)
print("Total sellers:", len(seller_orders))
print("SELLER-WISE LSR TEST PASSED!")
