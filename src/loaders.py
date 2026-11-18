import csv


def load_csv(path):
    """Read a CSV file and return a list of rows. Each row is a dictionary."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))