from ingest import load_orders, load_messages

seen = set()
good, rejected = load_orders("data/orders_week_02.csv", 2, seen)

print("Good orders:", len(good))
print("Rejected:", rejected)

# Look for the order with the rating of 6 (ORD-000358)
for o in good:
    if o["order_id"] == "ORD-000358":
        print("ORD-000358 kept, rating is:", o["rating"])

msgs = load_messages("data/messages_week_02.csv")
print("Messages:", len(msgs))