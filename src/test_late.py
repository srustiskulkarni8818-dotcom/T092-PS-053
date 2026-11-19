
from datetime import datetime, date
from metrics import is_late

promised = date(2026, 8, 7)

order_178 = datetime(2026, 8, 8, 23, 59, 59)
order_179 = datetime(2026, 8, 9, 0, 0, 0)

assert is_late(promised, order_178) is False
assert is_late(promised, order_179) is True

print("ORD-000178: NOT LATE - PASS")
print("ORD-000179: LATE - PASS")
print("Both tests passed!")
