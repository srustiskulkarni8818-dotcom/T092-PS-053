
from metrics import calculate_scr

# Create 200 sample orders
orders = []

for i in range(200):
    orders.append({
        "cancelled_by": None,
        "cancel_reason": None
    })

# Five qualifying seller cancellations
for i in range(5):
    orders[i]["cancelled_by"] = "SELLER"
    orders[i]["cancel_reason"] = "OUT_OF_STOCK"

# One excluded seller cancellation
orders[5]["cancelled_by"] = "SELLER"
orders[5]["cancel_reason"] = "BUYER_REQUEST"

# Another excluded seller cancellation
orders[6]["cancelled_by"] = "SELLER"
orders[6]["cancel_reason"] = "ADDRESS_UNSERVICEABLE"

result = calculate_scr(orders)

print("Total orders:", len(orders))
print("Expected SCR: 2.5%")
print("Calculated SCR:", result, "%")

assert result == 2.5
print("SCR TEST PASSED!")
