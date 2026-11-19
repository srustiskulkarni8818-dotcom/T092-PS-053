
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import calendar

from loaders import load_csv
from ingest import load_orders, load_messages
from appeals import AppealManager
from scorecard import build_scorecard
from tiers import assign_tier, apply_tier_review, TIER_EFFECTS
from outputs import (
    write_scorecards,
    write_penalty_ledger,
    write_state_transitions
)
from metrics import is_late

EXCLUDED_REASONS = {
    "BUYER_REQUEST",
    "ADDRESS_UNSERVICEABLE"
}
COURIER_REASONS = {"PICKUP_FAILED", "WEATHER_DELAY"}


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_datetime(value):
    if isinstance(value, datetime):
        return value
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def months_before(day, months):
    index = day.year * 12 + day.month - 1 - months
    year, month = divmod(index, 12)
    month += 1
    return day.replace(
        year=year,
        month=month,
        day=min(day.day, calendar.monthrange(year, month)[1])
    )


class MarketplaceEngine:

    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.sellers = []
        self.courier_events = []
        self.orders = []
        self.messages = []
        self.seen_ids = set()
        self.processed_weeks = set()
        self.penalized_weeks = set()
        self.appeals = AppealManager()
        self.scorecard_rows = []
        self.penalty_rows = []
        self.state_rows = []
        self.penalty_counter = 0
        self.review_dates = {}
        self.excluded_order_ids = set()
        self.pending_appeal_decisions = {}
        self.seller_states = {}
        self.suspension_dates = {}
        self.probation_start = {}
        self.watch_streak = {}

    def save_outputs(self):
        write_scorecards(self.scorecard_rows)
        write_penalty_ledger(self.penalty_rows)
        write_state_transitions(self.state_rows)

    def transition(self, seller_id, when, to_state, trigger):
        current = self.seller_states[seller_id]
        allowed = {
            "ACTIVE": {"SUSPENDED", "TERMINATED"},
            "SUSPENDED": {"PROBATION", "TERMINATED"},
            "PROBATION": {"ACTIVE", "SUSPENDED", "TERMINATED"},
            "TERMINATED": set()
        }
        if to_state not in allowed[current]:
            raise ValueError(
                f"Invalid state transition: {current} -> {to_state}"
            )
        self.seller_states[seller_id] = to_state
        self.state_rows.append({
            "seller_id": seller_id,
            "transition_date": when.isoformat(),
            "from_state": current,
            "to_state": to_state,
            "trigger": trigger
        })
        if to_state == "SUSPENDED":
            self.suspension_dates[seller_id] = when
            self.probation_start[seller_id] = None
        elif to_state == "PROBATION":
            self.probation_start[seller_id] = when
            self.watch_streak[seller_id] = 0
        elif to_state == "ACTIVE":
            self.probation_start[seller_id] = None

    def suspend(self, seller_id, when, trigger):
        state = self.seller_states[seller_id]
        if state in {"TERMINATED", "SUSPENDED"}:
            return
        previous = self.suspension_dates.get(seller_id)
        if (
            previous is not None
            and months_before(when, 6) <= previous <= when
        ):
            self.transition(
                seller_id, when, "TERMINATED",
                "SECOND_SUSPENSION_WITHIN_6_MONTHS"
            )
        else:
            self.transition(seller_id, when, "SUSPENDED", trigger)

    def create_penalty(
        self, seller_id, week_no, order_id,
        penalty_type, amount, capped_amount
    ):
        self.penalty_counter += 1
        row = {
            "penalty_id": f"PEN-{self.penalty_counter:06d}",
            "seller_id": seller_id,
            "week_no": week_no,
            "order_id": order_id,
            "penalty_type": penalty_type,
            "amount": f"{money(amount):.2f}",
            "amount_after_cap": f"{money(capped_amount):.2f}",
            "status": "LEVIED",
            "appeal_id": "",
            "reversal_date": ""
        }
        self.penalty_rows.append(row)
        return row

    def calculate_penalties_for_week(self, week_no, review_date):
        if week_no in self.penalized_weeks:
            raise ValueError(f"Week {week_no} already reviewed")

        week_start = review_date - timedelta(days=7)
        totals = {}

        for seller in self.sellers:
            seller_id = seller["seller_id"]
            orders = [
                o for o in self.orders
                if o["seller_id"] == seller_id
            ]
            placed = [
                o for o in orders
                if o["order_ts"] is not None
                and week_start <= o["order_ts"].date() < review_date
            ]
            weekly_gmv = sum(
                (money(o["gmv"]) for o in placed),
                Decimal("0.00")
            )

            late = [
                o for o in orders
                if o["shipped_ts"] is not None
                and week_start <= o["shipped_ts"].date() < review_date
                and o["order_id"] not in self.excluded_order_ids
                and is_late(o["promised"], o["shipped_ts"])
            ]
            late.sort(
                key=lambda o: (o["shipped_ts"], o["order_id"])
            )

            incidents = [
                {
                    "order_id": o["order_id"],
                    "type": "LATE_SHIPMENT",
                    "amount": Decimal("50.00"),
                    "timestamp": o["shipped_ts"]
                }
                for o in late[3:]
            ]

            for o in orders:
                cancelled = o["cancelled_ts"]
                if (
                    cancelled is not None
                    and week_start <= cancelled.date() < review_date
                    and o["cancelled_by"] == "SELLER"
                    and o["cancel_reason"] not in EXCLUDED_REASONS
                    and o["order_id"] not in self.excluded_order_ids
                ):
                    incidents.append({
                        "order_id": o["order_id"],
                        "type": "SELLER_CANCELLATION",
                        "amount": (
                            Decimal("200.00")
                            if o["prepaid"] else Decimal("100.00")
                        ),
                        "timestamp": cancelled
                    })

            incidents.sort(
                key=lambda x: (
                    x["timestamp"], x["order_id"], x["type"]
                )
            )

            cap = min(
                Decimal("5000.00"),
                money(weekly_gmv * Decimal("0.05"))
            )
            remaining = cap
            levied = Decimal("0.00")
            probation = (
                self.seller_states.get(seller_id) == "PROBATION"
            )

            for incident in incidents:
                amount = incident["amount"] * (
                    2 if probation else 1
                )
                charged = min(amount, remaining)
                remaining -= charged
                levied += charged

                self.create_penalty(
                    seller_id, week_no,
                    incident["order_id"],
                    incident["type"],
                    amount, charged
                )

            totals[seller_id] = {
                "gmv": weekly_gmv,
                "penalty": levied
            }

        self.review_dates[week_no] = review_date
        self.penalized_weeks.add(week_no)
        return totals

    def courier_evidence(self, order_id, decision_date):
        return any(
            event["order_id"] == order_id
            and event["event_type"] in COURIER_REASONS
            and parse_datetime(event["event_ts"]).date()
            <= decision_date
            for event in self.courier_events
        )

    def matching_penalties(self, appeal):
        return [
            p for p in self.penalty_rows
            if p["seller_id"] == appeal["seller_id"]
            and p["order_id"] == appeal["order_id"]
        ]

    def reconcile_appeal(self, appeal_id):
        if appeal_id not in self.pending_appeal_decisions:
            return

        appeal = self.appeals.appeals[appeal_id]
        decision = self.pending_appeal_decisions[appeal_id]
        penalties = self.matching_penalties(appeal)

        if not penalties:
            print(f"Appeal {appeal_id}: no matching penalty yet")
            return

        filing_date = appeal["appeal_date"]
        decision_date = decision["date"]
        levy_date = min(
            self.review_dates[int(p["week_no"])]
            for p in penalties
        )

        timely = (
            levy_date <= filing_date
            <= levy_date + timedelta(days=7)
        )

        if not timely:
            final_status = "REJECTED_LATE"
        elif self.courier_evidence(
            appeal["order_id"], decision_date
        ):
            final_status = "ACCEPTED"
        else:
            final_status = decision["requested"]

        appeal["status"] = final_status

        for penalty in penalties:
            penalty["appeal_id"] = appeal_id
            if final_status == "ACCEPTED":
                penalty["status"] = "REVERSED"
                penalty["reversal_date"] = (
                    decision_date.isoformat()
                )

        if final_status == "ACCEPTED":
            self.excluded_order_ids.add(
                appeal["order_id"]
            )

        print(
            f"Appeal {appeal_id}: {final_status}, "
            f"matched penalties: {len(penalties)}"
        )
        del self.pending_appeal_decisions[appeal_id]

    def review_tiers(self, review_date_text):
        review_date = parse_date(review_date_text)

        if not self.processed_weeks:
            raise ValueError("No weeks processed")

        week = max(self.processed_weeks)
        totals = self.calculate_penalties_for_week(
            week, review_date
        )

        for appeal_id in list(self.pending_appeal_decisions):
            self.reconcile_appeal(appeal_id)

        valid_orders = [
            o for o in self.orders
            if o["order_id"] not in self.excluded_order_ids
        ]
        week_start = review_date - timedelta(days=7)

        for seller in self.sellers:
            seller_id = seller["seller_id"]

            score = build_scorecard(
                seller_id, week,
                valid_orders, self.messages,
                review_date=review_date
            )

            age_weeks = (
                review_date - parse_date(seller["join_date"])
            ).days // 7

            target, breaches = assign_tier(
                score, seller["category"], age_weeks
            )

            if (
                score["unanswered_messages"]
                and (
                    score["response_hours"] is None
                    or score["response_hours"] <= 24
                )
            ):
                breaches += 1
                target = (
                    "WATCH" if breaches >= 2 else "SILVER"
                )

            state = self.seller_states[seller_id]

            if (
                state == "PROBATION"
                and self.probation_start[seller_id] is not None
                and review_date >= (
                    self.probation_start[seller_id]
                    + timedelta(weeks=4)
                )
            ):
                self.transition(
                    seller_id, review_date, "ACTIVE",
                    "PROBATION_COMPLETED"
                )

            weekly_orders = [
                o for o in valid_orders
                if o["seller_id"] == seller_id
                and o["order_ts"] is not None
                and week_start <= o["order_ts"].date() < review_date
            ]

            cancellations = sum(
                1 for o in weekly_orders
                if o["cancelled_ts"] is not None
                and o["cancelled_by"] == "SELLER"
                and o["cancel_reason"] not in EXCLUDED_REASONS
            )

            weekly_scr = (
                100 * cancellations / len(weekly_orders)
                if weekly_orders else 0.0
            )

            if target == "WATCH":
                self.watch_streak[seller_id] += 1
            else:
                self.watch_streak[seller_id] = 0

            if self.seller_states[seller_id] in {
                "ACTIVE", "PROBATION"
            }:
                if weekly_scr > 10:
                    self.suspend(
                        seller_id, review_date,
                        "WEEKLY_SCR_ABOVE_10_PERCENT"
                    )
                elif self.watch_streak[seller_id] >= 3:
                    self.suspend(
                        seller_id, review_date,
                        "THREE_CONSECUTIVE_WATCH_WEEKS"
                    )

            new_tier = apply_tier_review(
                seller["current_tier"], target
            )

            if (
                self.seller_states[seller_id] == "PROBATION"
                and new_tier in {"GOLD", "PLATINUM"}
            ):
                new_tier = "SILVER"

            seller["current_tier"] = new_tier
            effects = TIER_EFFECTS[new_tier]
            weekly = totals[seller_id]

            self.scorecard_rows.append({
                "seller_id": seller_id,
                "week_no": week,
                "review_date": str(review_date),
                "shipped_4w": score["shipped_count"],
                "lsr_pct": (
                    f'{score["lsr"]:.2f}'
                    if score["lsr"] is not None else ""
                ),
                "lsr_evaluated": str(
                    score["lsr"] is not None
                ).lower(),
                "scr_pct": f'{score["scr"]:.2f}',
                "return_rate_pct": (
                    f'{score["return_rate"]:.2f}'
                ),
                "median_response_hours": (
                    f'{score["response_hours"]:.2f}'
                    if score["response_hours"] is not None
                    else ""
                ),
                "avg_rating": (
                    f'{score["rating"]:.2f}'
                    if score["rating"] is not None else ""
                ),
                "rating_count": score["rating_count"],
                "breaches": breaches,
                "tier": new_tier,
                "commission_adj_pp": (
                    effects["commission_change"]
                ),
                "search_boost": (
                    f'{effects["search_boost"]:.2f}'
                ),
                "state": self.seller_states[seller_id],
                "week_gmv": f'{weekly["gmv"]:.2f}',
                "week_penalty_levied": (
                    f'{weekly["penalty"]:.2f}'
                )
            })

        self.save_outputs()
        print(
            f"Week {week} review completed: "
            f"{len(self.sellers)} sellers"
        )

    def decide_appeal(
        self, appeal_id, date_text, requested, note
    ):
        if appeal_id not in self.appeals.appeals:
            raise ValueError(
                f"Unknown appeal: {appeal_id}"
            )

        decision_date = parse_date(date_text)

        appeal = self.appeals.decide_appeal(
            appeal_id, date_text, requested, note
        )

        self.pending_appeal_decisions[appeal_id] = {
            "date": decision_date,
            "requested": requested,
            "note": note
        }

        self.reconcile_appeal(appeal_id)
        self.save_outputs()
        return appeal

    def execute(self, command):
        action, *args = command

        if action == "LOAD_SELLERS":
            self.sellers = load_csv(
                self.data_dir / args[0]
            )

            for seller in self.sellers:
                seller_id = seller["seller_id"]
                self.seller_states[seller_id] = "ACTIVE"

                prior = seller.get(
                    "prior_suspension_date", ""
                ).strip()

                self.suspension_dates[seller_id] = (
                    parse_date(prior) if prior else None
                )
                self.probation_start[seller_id] = None
                self.watch_streak[seller_id] = 0

            print("Loaded sellers:", len(self.sellers))

        elif action == "LOAD_COURIER_EVENTS":
            self.courier_events = load_csv(
                self.data_dir / args[0]
            )
            print(
                "Loaded courier events:",
                len(self.courier_events)
            )

        elif action == "PROCESS_WEEK":
            week = int(args[0])

            if week in self.processed_weeks:
                raise ValueError(
                    f"Week {week} already processed"
                )

            orders, rejected = load_orders(
                self.data_dir / args[1],
                week,
                self.seen_ids
            )
            messages = load_messages(
                self.data_dir / args[2]
            )

            for message in messages:
                message["week_no"] = week

            self.orders.extend(orders)
            self.messages.extend(messages)
            self.processed_weeks.add(week)

            print(
                f"Week {week:02d}: "
                f"{len(orders)} orders, "
                f"{len(messages)} messages, "
                f"{len(rejected)} rejected"
            )

        elif action == "REVIEW_TIERS":
            self.review_tiers(args[0])

        elif action == "APPEAL":
            self.appeals.submit_appeal(*args)
            print("Appeal submitted:", args[0])

        elif action == "DECIDE_APPEAL":
            self.decide_appeal(*args)

        elif action == "REINSTATE":
            when = parse_date(args[0])
            seller_id = args[1]

            if seller_id not in self.seller_states:
                raise ValueError(
                    f"Unknown seller: {seller_id}"
                )

            if self.seller_states[seller_id] != "SUSPENDED":
                raise ValueError(
                    f"Cannot reinstate {seller_id}: not suspended"
                )

            if when < (
                self.suspension_dates[seller_id]
                + timedelta(days=14)
            ):
                raise ValueError(
                    f"Cannot reinstate {seller_id} before 14 days"
                )

            self.transition(
                seller_id, when, "PROBATION",
                "REINSTATED_AFTER_14_DAYS"
            )
            self.save_outputs()
            print("Reinstated:", seller_id)

        elif action == "COUNTERFEIT_CONFIRMED":
            when = parse_date(args[0])
            seller_id = args[1]
            order_id = args[2]

            if seller_id not in self.seller_states:
                raise ValueError(
                    f"Unknown seller: {seller_id}"
                )

            if self.seller_states[seller_id] == "TERMINATED":
                raise ValueError(
                    f"Seller {seller_id} already terminated"
                )

            self.create_penalty(
                seller_id,
                max(self.processed_weeks, default=0),
                order_id,
                "COUNTERFEIT",
                Decimal("25000.00"),
                Decimal("25000.00")
            )

            self.suspend(
                seller_id, when, "COUNTERFEIT_CONFIRMED"
            )
            self.save_outputs()
            print("Counterfeit confirmed:", seller_id)

        elif action == "PRINT_SCORECARD":
            seller_id = args[0]

            if seller_id not in self.seller_states:
                raise ValueError(
                    f"Unknown seller: {seller_id}"
                )

            self.save_outputs()
            print(
                "Scorecards written:",
                len(self.scorecard_rows)
            )

        elif action == "PRINT_PENALTY_LEDGER":
            self.save_outputs()
            print(
                "Penalty ledger written:",
                len(self.penalty_rows)
            )

        elif action == "PRINT_STATES":
            self.save_outputs()
            print(
                "State transitions written:",
                len(self.state_rows)
            )

        else:
            raise ValueError(
                f"Unknown command: {action}"
            )
