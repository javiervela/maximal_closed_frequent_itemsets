import os
import csv
from typing import List, Dict, Set
from collections import defaultdict


################################################################################
# Transactions
################################################################################


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


################################################################################
# Frequent Itemsets
################################################################################


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


################################################################################
# Maximal and Closed Itemsets
################################################################################


def get_maximal_itemsets(
    L: Dict[int, Dict[frozenset, int]],
) -> Dict[frozenset, int]:
    """
    Extract maximal frequent itemsets (those with no frequent superset).

    Description:
    - For each level L(k), we check if each itemset is a strict subset of any larger frequent itemset in L(k+1).
    - If it is, then the itemset is not maximal and is removed from the list of maximal itemsets.

    Parameters:
    - L (Dict[int, Dict[frozenset, int]]): Dictionary of frequent itemsets.

    Returns:
    - (Dict[frozenset, int]): Dictionary containing maximal frequent itemsets.
    """

    # Initially, all itemsets from flattened L
    maximal_itemsets = {i: s for k, L_k in L.items() for i, s in L_k.items()}

    # For each level L(k)
    for k, _ in L.items():
        # For each itemset in L(k)
        for itemset in L.get(k):
            # For each larger itemset in L(k+1)
            for other in L.get(k + 1, []):
                # Strict subset (other is superset of itemset)
                if itemset < other:
                    # Itemset is not maximal
                    maximal_itemsets.pop(itemset, None)
                    break

    return maximal_itemsets


def get_closed_itemsets(
    L: Dict[int, Dict[frozenset, int]],
) -> Dict[frozenset, int]:
    """
    Extract closed frequent itemsets (those whose supersets have a different support).

    Description:
    - For each level L(k), we check if each itemset is a strict subset with the same support of any larger frequent itemset in L(k+1).
    - If it is, then the itemset is not closed and not added to the list of closed itemsets.

    Parameters:
    - L (Dict[int, Dict[frozenset, int]]): Dictionary of frequent itemsets.

    Returns:
    - (Dict[frozenset, int]): Dictionary containing closed frequent itemsets.
    """

    # Initially, no closed itemsets
    closed_itemsets = {}

    # For each level L(k)
    for k, _ in L.items():
        # For each itemset in L(k)
        for itemset, support in L.get(k).items():
            is_closed = True
            # For each larger itemset in L(k+1)
            # If there is no L(k+1), then the itemset is closed
            for other, other_support in L.get(k + 1, {}).items():
                # Strict subset (other is superset of itemset) with same support
                if itemset < other and support == other_support:
                    # Itemset is not closed
                    is_closed = False
                    break
            # If the itemset is closed, add it to the list of closed itemsets
            if is_closed:
                closed_itemsets[itemset] = support

    return closed_itemsets


################################################################################
# Others
################################################################################


def print_itemsets(
    frequent_itemsets: Dict[int, Dict[frozenset, int]],
    maximal_itemsets: Dict[frozenset, int],
    closed_itemsets: Dict[frozenset, int],
) -> None:
    """
    Print frequent itemsets, maximal frequent itemsets, and closed frequent itemsets.

    Parameters:
    - frequent_itemsets (Dict[int, Dict[frozenset, int]]): Dictionary of frequent itemsets.
    - maximal_itemsets (Dict[frozenset, int]): Dictionary of maximal frequent itemsets.
    - closed_itemsets (Dict[frozenset, int]): Dictionary of closed frequent itemsets.
    """

    print("------------------")
    print("Frequent Itemsets:")
    print("------------------")
    for k, L_k in frequent_itemsets.items():
        print(f"L({k}):")
        for itemset, count in L_k.items():
            print(f"  - {set(itemset)}: {count}")
    print()

    print("--------------------------")
    print("Maximal Frequent Itemsets:")
    print("--------------------------")
    for itemset, count in maximal_itemsets.items():
        print(f" - {set(itemset)}: {count}")
    print()

    print("--------------------------")
    print("Closed Frequent Itemsets:")
    print("--------------------------")
    for itemset, count in closed_itemsets.items():
        print(f" - {set(itemset)}: {count}")
    print()


################################################################################
# Main
################################################################################


if __name__ == "__main__":
    DATA_FILE = os.getenv("DATA_FILE", "data/data.csv")
    MIN_SUPPORT = int(os.getenv("MIN_SUPPORT", "5"))

    # T - List of transactions
    transactions = read_items(DATA_FILE)

    # T_index - Inverted index mapping each item to the set of transaction indices in which it appears
    transactions_index = build_transactions_inverted_index(transactions)

    frequent_itemsets = generate_frequent_itemsets(
        transactions, transactions_index, MIN_SUPPORT
    )

    maximal_itemsets = get_maximal_itemsets(frequent_itemsets)
    closed_itemsets = get_closed_itemsets(frequent_itemsets)

    print_itemsets(frequent_itemsets, maximal_itemsets, closed_itemsets)
