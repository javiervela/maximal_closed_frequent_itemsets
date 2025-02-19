import os
import csv
from typing import List, Dict


def read_items(filename: str) -> List[Dict]:
    """
    Read items from a CSV file
    """
    rows = []
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["items"] = set(row["items"])
            rows.append(row)
    return rows


if __name__ == "__main__":
    # TODO change for final data file
    DATA_FILE = os.getenv("DATA_FILE", "data/test.csv")
    data = read_items(DATA_FILE)

    print(data)
