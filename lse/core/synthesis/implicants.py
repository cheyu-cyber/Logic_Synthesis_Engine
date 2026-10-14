"""This module reports the total count of (essential) prime implicants.
Also reports the total number of ON-Set minterms and Off-Set maxterms.
"""
import re
from literal_minimized import covers, get_vars


def consensus(cube1, cube2, var):
    """
    Computes the consensus of two cubes with respect to a single variable.
    Returns the consensus cube if valid (no other conflicting literals), else None.
    """
    if var not in cube1 or var not in cube2:
        return None
    if cube1[var] == cube2[var]:
        return None  # Variable must appear inverted between the two cubes

    # Ensure no other variables have conflicting literals
    res = {}
    for v in set(cube1.keys()).union(set(cube2.keys())):
        if v == var:
            continue
        val1, val2 = cube1.get(v), cube2.get(v)
        if val1 is not None and val2 is not None and val1 != val2:
            return None  # Conflicting literal found elsewhere
        res[v] = val1 if val1 is not None else val2
    return res


def clean_absorptions(cubes):
    """Removes any cube that is absorbed by another cube in the list."""
    to_keep = []
    for i, c1 in enumerate(cubes):
        absorbed = False
        for j, c2 in enumerate(cubes):
            if i != j and covers(c2, c1):
                # Handle exact duplicates by keeping the lower index
                if c1 == c2 and j < i:
                    absorbed = True
                    break
                elif c1 != c2:
                    absorbed = True
                    break
        if not absorbed:
            to_keep.append(c1)
    return to_keep


def parse_term(term_str):
    """Parses a single product term string into a dictionary {var_name: bool}."""
    term_str = term_str.strip()
    if '*' in term_str or ' ' in term_str or 'AND' in term_str:
        tokens = [t for t in re.split(r'\*|\s+|\bAND\b', term_str) if t]
    else:
        # Matches single concatenated variables like A'BC, ~a~bc, x1'x2
        tokens = re.findall(r'[!~]?[A-Za-z][0-9]*\'?', term_str)

    cube = {}
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        is_negated = tok.startswith('!') or tok.startswith('~') or tok.endswith("'")
        var_name = tok.lstrip('!~').rstrip("'")
        if var_name:
            cube[var_name] = not is_negated
    return cube


def cube_to_string(cube):
    """Formats a cube dict back to a standard Boolean product term."""
    if not cube:
        return "1"  # Tautology
    return "".join(f"{v}" if val else f"{v}'" for v, val in sorted(cube.items()))


def get_pi(canonical_sop):
    """
    Computes all Prime Implicants from a canonical SOP string using Tison's Consensus Method.
    """
    # 1. Parse input SOP string into cube dictionaries
    raw_terms = [t.strip() for t in re.split(r'\+|\bOR\b', canonical_sop) if t.strip()]
    cubes = [parse_term(term) for term in raw_terms if term]

    # 2. Extract unique variable names
    all_vars = sorted(list({v for cube in cubes for v in cube.keys()}))

    # 3. Initial absorption pass
    cubes = clean_absorptions(cubes)

    # 4. Tison's Method: Iterate variable-by-variable
    for v in all_vars:
        new_consensus_cubes = []
        n = len(cubes)
        for i in range(n):
            for j in range(i + 1, n):
                cons = consensus(cubes[i], cubes[j], v)
                if cons is not None:
                    new_consensus_cubes.append(cons)

        if new_consensus_cubes:
            cubes.extend(new_consensus_cubes)
            cubes = clean_absorptions(cubes)

    # 5. Format results
    prime_implicants = [cube_to_string(c) for c in cubes]

    return prime_implicants


def get_epi(prime_implicants):

    prime_implicants.sort()
    var_names = get_vars(prime_implicants)

    F_init = []
    for term in prime_implicants:
        pattern = []
        for var in var_names:
            if var + "'" in term:
                pattern.append('0')
            elif var in term:
                pattern.append('1')
            else:
                pattern.append('-')
        F_init.append("".join(pattern))

    essential_pi = set()
    max_len = max(len(s) for s in F_init) if F_init else 0

    for pos in range(max_len):
        # Find all item indices that have '0' or '1' at the current position
        zeros = [i for i, item in enumerate(F_init) if pos < len(item) and item[pos] == '0']
        ones = [i for i, item in enumerate(F_init) if pos < len(item) and item[pos] == '1']

        # If '0' or '1' occurs in exactly one item at this position, keep its index
        if len(zeros) == 1:
            essential_pi.add(zeros[0])
        if len(ones) == 1:
            essential_pi.add(ones[0])

    epi = []
    for idx in essential_pi:
        epi.append(prime_implicants[idx])

    return epi


# # Example Use
# sop_input = "A'C' + B'C"
# num_pi = get_pi(sop_input)
# num_epi = get_epi(num_pi)
# print(f"Number of PIs: {len(num_pi)}")
# print(f"Number of EPIs: {len(num_epi)}")
