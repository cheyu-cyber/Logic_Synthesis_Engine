"""This module reports the total count of (essential) prime implicants.
Also reports the total number of ON-Set minterms and Off-Set maxterms.
"""
from lse.core.synthesis.literal_minimized import covers as covers_pattern, to_cubes


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


def covers(cube1, cube2):
    """Returns True if cube1 completely covers cube2 (every literal of cube1 is in cube2)."""
    return all(cube2.get(v) == val for v, val in cube1.items())


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


def minterm_cubes(minterms, names):
    """Turns minterm numbers (canonical.minterms) into cube dictionaries {var_name: bool}
    via literal_minimized.to_cubes (5 -> '101' -> {a: True, b: False, cin: True})."""
    return [{s: c == "1" for s, c in zip(names, cube)} for cube in sorted(to_cubes(minterms, len(names)))]


def cube_to_string(cube, names):
    """Formats a cube dict back to a standard Boolean product term."""
    if not cube:
        return "1"  # Tautology
    return "".join(f"{v}" if cube[v] else f"{v}'" for v in names if v in cube)


def term_to_pattern(term, names):
    """Inverse of cube_to_string: turns a product term back into a '01-' pattern over names.
    Literals appear in names order; backtracks so overlapping names (x1, x10) parse correctly."""
    if not names:
        return "" if term in ("", "1") else None
    var, later = names[0], names[1:]
    for literal, bit in ((var + "'", "0"), (var, "1")):
        if term.startswith(literal):
            rest = term_to_pattern(term[len(literal):], later)
            if rest is not None:
                return bit + rest
    rest = term_to_pattern(term, later)
    return None if rest is None else "-" + rest


def get_pi(minterms, names):
    """
    Computes all Prime Implicants from a canonical SOP string using Tison's Consensus Method.
    """
    # 1. Parse input SOP string into cube dictionaries
    cubes = minterm_cubes(minterms, names)

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
    prime_implicants = [cube_to_string(c, names) for c in cubes]

    return prime_implicants


def get_epi(prime_implicants, minterms, names):
    """A prime implicant is essential if it is the only one covering some ON-set minterm."""

    prime_implicants.sort()

    F_init = []
    for term in prime_implicants:
        F_init.append(term_to_pattern(term, names))

    essential_pi = set()

    for row in to_cubes(minterms, len(names)):
        # Find all item indices whose pattern covers the current ON-set minterm
        covering = [i for i, item in enumerate(F_init) if covers_pattern(item, row)]

        # If exactly one item covers this minterm, it is essential; keep its index
        if len(covering) == 1:
            essential_pi.add(covering[0])

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
