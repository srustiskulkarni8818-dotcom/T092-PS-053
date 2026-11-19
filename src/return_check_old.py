
from metrics import calculate_return_rate

# Create 100 sample orders
orders = []

for i in range(100):
    orders.append({
        "return_reason": ""
    })

# Mark 10 orders as returned
for i in range(10):
    orders[i]["return_reason"] = "DAMAGED_ITEM"

result = calculate_return_rate(orders)

print("Total orders:", len(orders))
print("Returned orders: 10")
print("Expected Return Rate: 10.0%")
print("Calculated Return Rate:", result, "%")

assert result == 10.0
print("RETURN RATE TEST PASSED!")
