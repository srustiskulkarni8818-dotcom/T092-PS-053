
import csv
from pathlib import Path

SCORECARD_COLUMNS = [
    "seller_id",
    "week_no",
    "review_date",
    "shipped_4w",
    "lsr_pct",
    "lsr_evaluated",
    "scr_pct",
    "return_rate_pct",
    "median_response_hours",
    "avg_rating",
    "rating_count",
    "breaches",
    "tier",
    "commission_adj_pp",
    "search_boost",
    "state",
    "week_gmv",
    "week_penalty_levied",
]

PENALTY_COLUMNS = [
    "penalty_id",
    "seller_id",
    "week_no",
    "order_id",
    "penalty_type",
    "amount",
    "amount_after_cap",
    "status",
    "appeal_id",
    "reversal_date",
]

STATE_COLUMNS = [
    "seller_id",
    "transition_date",
    "from_state",
    "to_state",
    "trigger",
]


def write_csv(path, columns, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_scorecards(rows, output_dir="output"):
    rows = sorted(
        rows,
        key=lambda row: (
            row["seller_id"],
            int(row["week_no"])
        )
    )

    write_csv(
        Path(output_dir) / "scorecards.csv",
        SCORECARD_COLUMNS,
        rows
    )


def write_penalty_ledger(rows, output_dir="output"):
    write_csv(
        Path(output_dir) / "penalty_ledger.csv",
        PENALTY_COLUMNS,
        rows
    )


def write_state_transitions(rows, output_dir="output"):
    write_csv(
        Path(output_dir) / "state_transitions.csv",
        STATE_COLUMNS,
        rows
    )
