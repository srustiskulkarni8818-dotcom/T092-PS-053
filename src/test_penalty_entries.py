
from datetime import date, datetime
from penalties import create_penalty_entries

orders = []

for i in range(1, 6):
    orders.append({
        "order_id": f"ORD-{i:03d}",
        "seller_id": "SEL-001",
        "promised": date(2026, 11, 16),
        "shipped_ts": datetime(2026, 11, 18, 12, i),
        "cancelled_by": "",
        "cancel_reason": "",
        "prepaid": False
    })

orders.append({
    "order_id": "ORD-006",
    "seller_id": "SEL-001",
    "promised": None,
    "shipped_ts": None,
    "cancelled_by": "SELLER",
    "cancel_reason": "OUT_OF_STOCK",
    "prepaid": True
})

entries = create_penalty_entries(orders, 12)

print("PENALTY LEDGER TEST")
print("-" * 55)

for entry in entries:
    print(entry)

assert len(entries) == 3
assert entries[0]["order_id"] == "ORD-004"
assert entries[1]["order_id"] == "ORD-005"
assert entries[2]["order_id"] == "ORD-006"
assert sum(entry["amount"] for entry in entries) == 300

print("-" * 55)
print("PENALTY LEDGER TEST PASSED!")
