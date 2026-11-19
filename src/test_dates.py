
from datetime import date, datetime
from metrics import parse_date, parse_timestamp

# Test 1: Convert promised shipping date
promised = parse_date("2026-08-04")

assert promised == date(2026, 8, 4)
print("DATE CONVERSION PASSED!")

# Test 2: Convert shipped timestamp
shipped = parse_timestamp("2026-08-03 08:00:00")

assert shipped == datetime(2026, 8, 3, 8, 0, 0)
print("TIMESTAMP CONVERSION PASSED!")

# Test 3: Handle empty dates
assert parse_date("") is None
print("EMPTY DATE TEST PASSED!")

# Test 4: Handle empty timestamps
assert parse_timestamp("") is None
print("EMPTY TIMESTAMP TEST PASSED!")

print("ALL DATE TESTS PASSED!")
