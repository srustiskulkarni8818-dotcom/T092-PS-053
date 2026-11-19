
from datetime import datetime


def parse_appeal_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


class AppealManager:
    def __init__(self):
        self.appeals = {}

    def submit_appeal(
        self,
        appeal_id,
        appeal_date,
        seller_id,
        order_id,
        reason,
        evidence_flag
    ):
        """Register a seller appeal."""

        if appeal_id in self.appeals:
            raise ValueError("Duplicate appeal ID")

        appeal = {
            "appeal_id": appeal_id,
            "appeal_date": parse_appeal_date(appeal_date),
            "seller_id": seller_id,
            "order_id": order_id,
            "reason": reason,
            "evidence_flag": evidence_flag.lower() == "true",
            "status": "PENDING",
            "decision_date": None,
            "decision_note": ""
        }

        self.appeals[appeal_id] = appeal

        return appeal

    def decide_appeal(
        self,
        appeal_id,
        decision_date,
        decision,
        note
    ):
        """Record an appeal decision."""

        if appeal_id not in self.appeals:
            raise ValueError("Appeal ID not found")

        appeal = self.appeals[appeal_id]

        if appeal["status"] != "PENDING":
            raise ValueError("Appeal already decided")

        if decision not in {"ACCEPTED", "REJECTED"}:
            raise ValueError("Invalid appeal decision")

        decided_on = parse_appeal_date(decision_date)

        if decided_on < appeal["appeal_date"]:
            raise ValueError("Decision cannot predate appeal")

        appeal["status"] = decision
        appeal["decision_date"] = decided_on
        appeal["decision_note"] = note

        return appeal
