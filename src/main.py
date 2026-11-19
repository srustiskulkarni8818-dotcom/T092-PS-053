from ingest import load_orders, load_messages
from metrics import calculate_lsr
def read_commands(path):
    """Read commands.txt and return a list of commands.
    Each command is a list: ['COMMAND_NAME', 'arg1', 'arg2', ...]"""
    commands = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue  # skip blank lines and comments
            commands.append(line.split("|"))
    return commands


if __name__ == "__main__":
    commands = read_commands("data/commands.txt")
    print("Number of commands:", len(commands))
    print("First command:", commands[0])
    print("Fourth command:", commands[3])


    
    seen_ids = set()
    all_orders = []
    all_rejected = []

    print()
    print("VALIDATING ALL 12 WEEKS")
    print("-" * 50)

    for week in range(1, 13):
        filename = f"data/orders_week_{week:02d}.csv"

        orders, rejected = load_orders(
            filename,
            week,
            seen_ids
        )

        all_orders.extend(orders)
        all_rejected.extend(rejected)

        print(
            f"Week {week:02d} | "
            f"Valid: {len(orders)} | "
            f"Rejected: {len(rejected)}"
        )

    print("-" * 50)
    print("Total valid orders:", len(all_orders))
    print("Total rejected orders:", len(all_rejected))
    print("Unique order IDs:", len(seen_ids))
    print("Rejected details:", all_rejected)
    print("ALL 12 WEEKS VALIDATED!")


    # Calculate LSR for each seller using validated orders
    from collections import defaultdict

    seller_orders = defaultdict(list)

    # Use Weeks 9-12 for the Week 12 review
    for order in all_orders:
        if 9 <= order["week_no"] <= 12:
            seller_orders[order["seller_id"]].append(order)

    print()
    print("WEEK 12 - FOUR-WEEK LSR REPORT")
    print("-" * 60)

    for seller_id in sorted(seller_orders):
        orders = seller_orders[seller_id]

        shipped_count = sum(
            1 for order in orders
            if order["shipped_ts"] is not None
        )

        if shipped_count < 20:
            result = "NOT EVALUATED"
        else:
            lsr = calculate_lsr(orders)
            result = f"{lsr}%"

        print(
            f"{seller_id} | "
            f"Shipped: {shipped_count} | "
            f"LSR: {result}"
        )

    print("-" * 60)
    print("VALIDATED SELLER LSR REPORT COMPLETED!")

    
    # Week 12 return rate uses Weeks 5 through 12
    from metrics import calculate_return_rate

    return_orders_by_seller = defaultdict(list)

    for order in all_orders:
        if 5 <= order["week_no"] <= 12:
            return_orders_by_seller[order["seller_id"]].append(order)

    print()
    print("WEEK 12 - EIGHT-WEEK RETURN RATE REPORT")
    print("-" * 65)

    for seller_id in sorted(return_orders_by_seller):
        orders = return_orders_by_seller[seller_id]

        delivered_count = sum(
            1 for order in orders
            if order["delivered_ts"] is not None
        )

        return_rate = calculate_return_rate(orders)

        print(
            f"{seller_id} | "
            f"Delivered: {delivered_count} | "
            f"Return Rate: {return_rate}%"
        )

    print("-" * 65)
    print("SELLER RETURN RATE REPORT COMPLETED!")


    # Calculate Week 12 SCR using Weeks 9 through 12
    from metrics import calculate_scr

    print()
    print("WEEK 12 - FOUR-WEEK SCR REPORT")
    print("-" * 60)

    for seller_id in sorted(seller_orders):
        orders = seller_orders[seller_id]

        total_orders = len(orders)
        scr = calculate_scr(orders)

        if scr > 2.5:
            status = "BREACH"
        else:
            status = "OK"

        print(
            f"{seller_id} | "
            f"Orders: {total_orders} | "
            f"SCR: {scr}% | "
            f"Status: {status}"
        )

    print("-" * 60)
    print("SELLER SCR REPORT COMPLETED!")


    # Calculate seller ratings using Weeks 5 through 12
    from metrics import calculate_rating

    print()
    print("WEEK 12 - EIGHT-WEEK SELLER RATING REPORT")
    print("-" * 65)

    for seller_id in sorted(return_orders_by_seller):
        orders = return_orders_by_seller[seller_id]

        rating_count = sum(
            1 for order in orders
            if order["rating"] is not None
        )

        average_rating = calculate_rating(orders)

        if average_rating is None:
            status = "NOT EVALUATED"
            rating_display = "N/A"
        elif average_rating < 3.8:
            status = "BREACH"
            rating_display = str(average_rating)
        else:
            status = "OK"
            rating_display = str(average_rating)

        print(
            f"{seller_id} | "
            f"Ratings: {rating_count} | "
            f"Average: {rating_display} | "
            f"Status: {status}"
        )

    print("-" * 65)
    print("SELLER RATING REPORT COMPLETED!")


    from metrics import calculate_response_time

    all_messages = []

    for week in range(1, 13):
        filename = f"data/messages_week_{week:02d}.csv"

        messages = load_messages(filename)

        for message in messages:
            message["week_no"] = week

        all_messages.extend(messages)

    print()
    print("WEEK 12 - SELLER RESPONSE TIME REPORT")
    print("-" * 65)

    week_12_messages = [
        message for message in all_messages
        if message["week_no"] == 12
    ]

    for seller_id in sorted(seller_orders):
        seller_messages = [
            message for message in week_12_messages
            if message["seller_id"] == seller_id
        ]

        median_hours = calculate_response_time(seller_messages)

        if median_hours is None:
            result = "N/A"
            status = "NOT EVALUATED"
        elif median_hours > 24:
            result = f"{median_hours} hours"
            status = "BREACH"
        elif median_hours > 12:
            result = f"{median_hours} hours"
            status = "ABOVE TARGET"
        else:
            result = f"{median_hours} hours"
            status = "OK"

        print(
            f"{seller_id} | "
            f"Median: {result} | "
            f"Status: {status}"
        )

    print("-" * 65)
    print("SELLER RESPONSE TIME REPORT COMPLETED!")


    from scorecard import build_scorecard

    print()
    print("WEEK 12 - COMBINED SELLER SCORECARD")
    print("-" * 65)

    seller_ids = sorted({
        order["seller_id"] for order in all_orders
    })

    for seller_id in seller_ids:
        scorecard = build_scorecard(
            seller_id,
            12,
            all_orders,
            all_messages
        )

        print(
            f"{seller_id} | "
            f"LSR: {scorecard['lsr']} | "
            f"SCR: {scorecard['scr']}% | "
            f"Returns: {scorecard['return_rate']}% | "
            f"Rating: {scorecard['rating']} | "
            f"Response: {scorecard['response_hours']} hrs"
        )

    print("-" * 65)
    print("COMBINED SCORECARD TEST COMPLETED!")

    
    from tiers import assign_tier, TIER_EFFECTS

    print()
    print("WEEK 12 - SELLER PERFORMANCE TIERS")
    print("-" * 75)

    for seller_id in seller_ids:
        scorecard = build_scorecard(
            seller_id,
            12,
            all_orders,
            all_messages
        )

        target_tier, breaches = assign_tier(
            scorecard,
            category="GENERAL",
            seller_age_weeks=12
        )

        effects = TIER_EFFECTS[target_tier]

        print(
            f"{seller_id} | "
            f"Target: {target_tier} | "
            f"Breaches: {breaches} | "
            f"Commission change: {effects['commission_change']:+} pp | "
            f"Search boost: {effects['search_boost']}x"
        )

    print("-" * 75)
    print("SELLER TIER REPORT COMPLETED!")


    from engine import MarketplaceEngine

    print()
    print("=" * 60)
    print("MARKETPLACE COMMAND ENGINE")
    print("=" * 60)

    engine = MarketplaceEngine()

    for command in commands:
        engine.execute(command)

    print("=" * 60)
    print("COMMAND PROCESSING COMPLETED!")
    print("Processed weeks:", len(engine.processed_weeks))
    print("Total orders:", len(engine.orders))
    print("Total messages:", len(engine.messages))
    print("Total appeals:", len(engine.appeals.appeals))








