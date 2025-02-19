import os
import csv
from typing import List, Dict, Set
from itertools import combinations
from collections import defaultdict


def read_items(filename: str) -> List[Set[str]]:
    """
    Read items from a CSV file where each row represents a transaction.
    """
    transactions = []
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            items = set(row["items"])
            transactions.append(items)
    return transactions


def get_frequent_itemsets_apriori(
    T: List[Set[str]], epsilon: int
) -> List[Dict[frozenset, int]]:
    """
    Compute frequent itemsets using the Apriori algorithm.

    Parameters:
    - T: List of transactions where each transaction is a set of items.
    - epsilon: Minimum support threshold.

    Returns:
    - List of dictionaries where each dictionary contains frequent itemsets
      of size k and their support count.
    """

    # L - Frequent itemsets
    L = []

    # C(1) - Candidate itemsets of size 1
    # Generate C(1): all unique items in transactions
    C_1 = defaultdict(int)
    for t in T:
        for item in t:
            C_1[frozenset([item])] += 1
    # Filter by epsilon
    # L(1) - Frequent itemsets of size 1
    L_1 = {k: v for k, v in C_1.items() if v >= epsilon}

    L.append(L_1)

    # k - Size of itemsets
    k = 2
    # L(k-1) - Frequent itemsets of size k-1
    L_k_1 = L[0]

    while L_k_1:
        # C(k) - Candidate itemsets of size k
        # Generate C(k): join L(k-1) with L(k-1) and filter by size k
        C_k = set(
            frozenset(a | b) for a, b in combinations(L_k_1, 2) if len(a | b) == k
        )

        # Count support of each itemset in C(k)
        count = defaultdict(int)
        for t in T:
            for c in C_k:
                if c.issubset(t):
                    count[c] += 1

        # Filter by epsilon
        # L(k) - Frequent itemsets of size k
        L_k = {x: v for x, v in count.items() if v >= epsilon}

        if L_k:
            L.append(L_k)

        # Update k and L(k-1)
        k += 1
        L_k_1 = L_k

    return L

if __name__ == "__main__":
    # TODO change for final data file
    DATA_FILE = os.getenv("DATA_FILE", "data/test.csv")
    MIN_SUPPORT = int(os.getenv("MIN_SUPPORT", "2"))

    # T - List of transactions
    transactions = read_items(DATA_FILE)

    # L - Frequent itemsets
    L = get_frequent_itemsets_apriori(transactions, MIN_SUPPORT)
    # Flatten [L(1), L(2), ..., L(k)]
    frequent_itemsets = {k: v for d in L for k, v in d.items()}

    print("Frequent Itemsets:")
    for k_1, L_k in enumerate(L):
        print(f"\nL({ k_1 + 1}): ")
        for itemset, support in L_k.items():
            print(f"\t-{set(itemset)}: {support}")
