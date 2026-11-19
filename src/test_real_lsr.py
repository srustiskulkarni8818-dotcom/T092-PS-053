
import csv

from metrics import (
    calculate_lsr,
    parse_date,
    parse_timestamp
)

orders = []

with open(
    "data/orders_week_01.csv",
    "r",
    newline="",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        orders.append({
            "promised": parse_date(
                row["promised_ship_date"]
            ),
            "shipped_ts": parse_timestamp(
                row["shipped_ts"]
            )
        })

shipped_orders = [
    order for order in orders
    if order["shipped_ts"] is not None
]

result = calculate_lsr(orders)

print("Total orders:", len(orders))
print("Shipped orders:", len(shipped_orders))
print("Late Shipment Rate:", result, "%")

assert 0 <= result <= 100

print("REAL CSV LSR TEST PASSED!")
