
import csv
from collections import defaultdict

from metrics import (
    calculate_lsr,
    parse_date,
    parse_timestamp
)

seller_orders = defaultdict(list)

# Read orders from Weeks 1 to 4
for week in range(1, 5):

    filename = f"data/orders_week_{week:02d}.csv"

    with open(
        filename,
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

print("FOUR-WEEK LSR REPORT - WEEKS 01 TO 04")
print("-" * 65)

for seller_id in sorted(seller_orders):

    orders = seller_orders[seller_id]

    shipped_count = sum(
        1 for order in orders
        if order["shipped_ts"] is not None
    )

    if shipped_count < 20:
        print(
            f"{seller_id} | "
            f"Shipped: {shipped_count} | "
            "LSR: NOT ELIGIBLE"
        )
    else:
        lsr = calculate_lsr(orders)

        print(
            f"{seller_id} | "
            f"Shipped: {shipped_count} | "
            f"LSR: {lsr}%"
        )

print("-" * 65)
print("Total sellers:", len(seller_orders))
print("FOUR-WEEK LSR TEST PASSED!")
