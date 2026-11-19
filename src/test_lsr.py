
from datetime import date, datetime
from metrics import calculate_lsr

orders = [
    {
        "promised": date(2026, 8, 7),
        "shipped_ts": datetime(2026, 8, 7, 15, 0, 0)
    },
    {
        "promised": date(2026, 8, 7),
        "shipped_ts": datetime(2026, 8, 8, 23, 59, 59)
    },
    {
        "promised": date(2026, 8, 7),
        "shipped_ts": datetime(2026, 8, 9, 0, 0, 0)
    },
    {
        "promised": date(2026, 8, 7),
        "shipped_ts": datetime(2026, 8, 10, 10, 0, 0)
    }
]

result = calculate_lsr(orders)

print("Total shipped orders:", len(orders))
print("Expected LSR: 50.0%")
print("Calculated LSR:", result, "%")

assert result == 50.0
print("LSR TEST PASSED!")
