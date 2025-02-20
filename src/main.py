import os
import csv
from typing import List, Dict, Set
from itertools import combinations
from collections import defaultdict


def read_items(filename: str) -> List[Set[str]]:
    """
    Read items from a CSV file where each row represents a transaction.
    """
    T = []
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            items = set(row["items"])
            T.append(items)
    return T


def build_transactions_inverted_index(T: List[Set[str]]) -> Dict[str, Set[int]]:
    """
    Build an inverted index mapping each item to the set of transaction indices in which it appears.
    """
    T_index = defaultdict(set)
    for idx, transaction in enumerate(T):
        for item in transaction:
            T_index[item].add(idx)
    return T_index


def compute_support(
    itemset: Set[str],
    T_index: Dict[str, Set[int]],
) -> int:
    """
    Compute the support of an itemset by intersecting the transaction sets of its items.

    Parameters:
    - itemset (Set[str]): Itemset for which to compute support.
    - T_index (Dict[str, Set[int]]): Inverted index mapping each item to the set of transaction indices in which it appears.

    Returns:
    - (int): Support count of the itemset.
    """
    # Get the transaction sets for each item
    sets = [T_index[item] for item in itemset if item in T_index]
    if not sets:
        return 0
    # Intersection of all transaction sets gives the transactions that contain the entire itemset.
    common_transactions = set.intersection(*sets)
    return len(common_transactions)


def find_frequent_sets_rec(
    T_index: Dict[str, Set[int]],
    min_support: int,
    current_itemset: Set[str],
    remaining_items: Set[str],
    k: int,
) -> Dict[int, Dict[frozenset, int]]:
    """
    Recursively find frequent itemsets using a depth-first search.

    Parameters:
    - T_index (Dict[str, Set[int]]): Inverted index mapping each item to the set of transaction indices in which it appears.
    - min_support (int): Minimum support threshold.
    - current_itemset (Set[str]): Current itemset being explored.
    - remaining_items (Set[str]): Remaining items to explore.
    - k (int): Current level of recursion.

    Returns:
    - (Dict[int, Dict[frozenset, int]]): Dictionary of frequent itemsets from the subtree at the current level.
    """

    # L(k) - Frequent itemsets of size k (this level of recursion)
    # L_rec - Frequent itemsets of current recursions
    L_rec = defaultdict(dict)

    # For each item in the remaining items
    for item in remaining_items:

        # Create a new itemset by adding the item
        new_set = current_itemset | {item}

        # Count support of the new itemset
        support = compute_support(new_set, T_index)

        # If the new itemset is frequent
        # By only considering frequent itemsets, we avoid generating infrequent itemsets
        if support >= min_support:

            # Add the itemset to the set of frequent itemsets
            L_rec[k][frozenset(new_set)] = support

            # Calculate the remaining items for the next recursion
            # The remaining items are those that are lexicographically greater than the current item
            new_remaining = {x for x in remaining_items if x > item}

            # This, would explore duplicates like (A, B) and (B, A)
            # new_remaining = remaining_items - {item}

            # If there are no remaining items, do not explore further this branch
            if not new_remaining:
                continue

            # Recursively find frequent itemsets
            L_rec_new = find_frequent_sets_rec(
                T_index, min_support, new_set, new_remaining, k + 1
            )

            # Merge the results of the recursion
            for key, value in L_rec_new.items():
                if key in L_rec:
                    L_rec[key].update(value)
                else:
                    L_rec[key] = value

    if not L_rec.get(k):
        return {}

    return L_rec


def generate_frequent_itemsets(
    T: List[Set[str]],
    T_index: Dict[str, Set[int]],
    min_support: int,
) -> Dict[int, Dict[frozenset, int]]:
    """
    Generate all frequent itemsets using a recursive depth-first search strategy.

    Parameters:
    - T (List[Set[str]]): List of transactions where each transaction is a set of items.
    - T_index (Dict[str, Set[int]]): Inverted index mapping each item to the set of transaction indices in which it appears.
    - min_support (int): Minimum support threshold.

    Returns:
    - (Dict[int, Dict[frozenset, int]]): Dictionary of frequent itemsets.
    """

    # L - Frequent itemsets
    L = {}

    # C(1) - Candidate itemsets of size 1
    # Generate C(1): all unique items in transactions
    C_1 = defaultdict(int)
    for t in T:
        for item in t:
            C_1[item] += 1

    # Filter by min_support
    # L(1) - Frequent itemsets of size 1
    L[1] = {item: support for item, support in C_1.items() if support >= min_support}

    # Start mining from single-item frequent sets
    L = find_frequent_sets_rec(T_index, min_support, set(), L[1], 1)

    return L


if __name__ == "__main__":
    # TODO change for final data file
    DATA_FILE = os.getenv("DATA_FILE", "data/test.csv")
    MIN_SUPPORT = int(os.getenv("MIN_SUPPORT", "2"))

    # T - List of transactions
    transactions = read_items(DATA_FILE)

    # T_index - Inverted index mapping each item to the set of transaction indices in which it appears
    transactions_index = build_transactions_inverted_index(transactions)

    frequent_itemsets = generate_frequent_itemsets(
        transactions, transactions_index, MIN_SUPPORT
    )

    print("Frequent Itemsets:")
    for k, L_k in frequent_itemsets.items():
        print(f"\tL({k + 1}):")
        for itemset, count in L_k.items():
            print(f"\t\t- {set(itemset)}: {count}")
