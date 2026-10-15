"""Literal Minimized SOP/POS forms synthesis module.
Using an Espresso-like minimization algorithm.
"""


def minterms_of_cube(cube):
    """Expands a positional cube string (e.g., '0-1')
    into binary minterm strings."""
    results = ['']
    for char in cube:
        if char == '-':
            results = [r + '0' for r in results] + [r + '1' for r in results]
        else:
            results = [r + char for r in results]
    return set(results)


def intersects(c1, c2):
    """Checks if two cubes intersect in at least one common minterm."""
    for b1, b2 in zip(c1, c2):
        if (b1 == '0' and b2 == '1') or (b1 == '1' and b2 == '0'):
            return False
    return True


def covers(c1, c2):
    """Returns True if cube c1 completely covers cube c2."""
    for b1, b2 in zip(c1, c2):
        if b1 != '-' and b1 != b2:
            return False
    return True


def bounding_cube(minterms):
    """Finds the smallest cube enclosing a set of binary minterm strings."""
    if not minterms:
        return None
    minterms_list = list(minterms)
    num_vars = len(minterms_list[0])
    res = []
    for i in range(num_vars):
        vals = {m[i] for m in minterms_list}
        res.append(vals.pop() if len(vals) == 1 else '-')
    return "".join(res)


# =====================================================================
# 1. EXPAND STEP
# =====================================================================
def expand_cube(cube, R):
    """
    Expands a single cube by replacing 0/1 with '-' variable by variable,
    ensuring it does not intersect any cube in the OFF-set R.
    """
    c = list(cube)
    for i in range(len(c)):
        if c[i] == '-':
            continue
        original = c[i]
        c[i] = '-'
        candidate = "".join(c)
        # Revert if candidate cube hits the OFF-set
        if any(intersects(candidate, r_cube) for r_cube in R):
            c[i] = original
    return "".join(c)


def expand_cover(F, R):
    """Expands all cubes in cover F and removes resulting redundant cubes."""
    new_F = []
    # Sort: process smaller cubes (fewer '-') first
    sorted_cubes = sorted(list(F), key=lambda x: x.count('-'))

    for c in sorted_cubes:
        if any(covers(existing, c) for existing in new_F):
            continue
        expanded = expand_cube(c, R)
        new_F = [e for e in new_F if not covers(expanded, e)]
        new_F.append(expanded)

    return list(set(new_F))


# =====================================================================
# 2. IRREDUNDANT COVER STEP
# =====================================================================
def irredundant_cover(F, D=set()):
    """
    Removes cubes from F that are completely covered by the union of
    all other cubes in F and the Don't-Care set D.
    """
    F_list = list(F)
    result = []

    for i, c in enumerate(F_list):
        remaining_cubes = result + F_list[i + 1:] + list(D)
        other_minterms = set().union(*(minterms_of_cube(o)
                                       for o in remaining_cubes))
        c_minterms = minterms_of_cube(c)

        # If not fully covered by other cubes, keep it
        if not c_minterms.issubset(other_minterms):
            result.append(c)

    return result


# =====================================================================
# 3. REDUCE STEP
# =====================================================================
def reduce_cube(c, F, D=set()):
    """
    Shrinks cube c to the smallest sub-cube containing all minterms of c
    that are NOT covered by (F \\ {c}) U D (its relative essential minterms).
    """
    c_minterms = minterms_of_cube(c)
    other_cubes = [x for x in F if x != c] + list(D)
    other_minterms = set().union(*(minterms_of_cube(o) for o in other_cubes))

    essential_minterms = c_minterms - other_minterms
    if not essential_minterms:
        return None  # Entirely redundant
    return bounding_cube(essential_minterms)


def reduce_cover(F, D=set()):
    """Reduces every cube in cover F sequence-wise."""
    F_current = list(F)
    for i, c in enumerate(F_current):
        reduced = reduce_cube(c, F_current, D)
        F_current[i] = reduced
    return [c for c in F_current if c is not None]


# =====================================================================
# 4. MAIN ESPRESSO LOOP
# =====================================================================
def compute_cost(F):
    """Cost metric: (number of cubes, total literals)."""
    num_cubes = len(F)
    num_literals = sum(c.count('0') + c.count('1') for c in F)
    return (num_cubes, num_literals)


def espresso_minimize(F_init, R_off, D_dont_care=set()):
    """
    Main Espresso loop: EXPAND -> IRREDUNDANT -> REDUCE
    ~ loop until cost converges ~
    """
    initial_cost = compute_cost(F_init)
    # print("Initial cost: ", initial_cost)

    F = expand_cover(F_init, R_off)
    F = irredundant_cover(F, D_dont_care)
    best_cost = compute_cost(F)

    while True:
        F_red = reduce_cover(F, D_dont_care)
        F_exp = expand_cover(F_red, R_off)
        F_irr = irredundant_cover(F_exp, D_dont_care)
        new_cost = compute_cost(F_irr)

        # Stop if no improvement in cube or literal count
        if new_cost >= best_cost:
            break
        F = F_irr
        best_cost = new_cost

    cost_reduction = tuple(a - b for a, b in zip(initial_cost, best_cost))

    return F, cost_reduction


# =====================================================================
# WRAPPER & HELPER FUNCTIONS
# =====================================================================
def to_cubes(rows, num_vars):
    """Row numbers -> positional cubes, first input as the MSB (5 -> '101')."""
    return {"".join(str(m >> (num_vars - 1 - i) & 1) for i in range(num_vars)) for m in rows}




def minimize_sop(minterms, var_names):
    """Minimizes an SOP string expression (e.g. "A'B'C + A'BC + AB'C")."""

    num_vars = len(var_names)

    # 1. ON-set cubes (F) and OFF-set (R)
    F_init = to_cubes(minterms, num_vars)
    R_off = minterms_of_cube('-' * num_vars) - F_init

    # 2. Run Espresso algorithm
    optimized_cubes, cost_reduction = espresso_minimize(F_init, R_off)

    # 3. Convert output cubes back to Boolean algebraic string
    sop_terms = []
    for c in sorted(optimized_cubes):
        term = []
        for i, char in enumerate(c):
            if char == '1':
                term.append(var_names[i])
            elif char == '0':
                term.append(f"{var_names[i]}'")
        sop_terms.append("".join(term) if term else "1")

    final_exp = " + ".join(sop_terms) if sop_terms else "0"

    return final_exp, cost_reduction


def minimize_pos(maxterms, var_names):
    """Minimizes an POS string expression (e.g. "A'+B'+C * A'+B+C)."""

    num_vars = len(var_names)

    # 1. OFF-set cubes (F') and ON-set (R)
    F_off = to_cubes(maxterms, num_vars)
    # F_init_off_set = all_minterms - on_minterms
    R_on = minterms_of_cube('-' * num_vars) - F_off

    # 2. Run Espresso algorithm
    optimized_cubes, cost_reduction = espresso_minimize(F_off, R_on)

    # 3. Convert output cubes back to Boolean algebraic string
    pos_terms = []
    for c in sorted(optimized_cubes):
        term = []
        for i, char in enumerate(c):
            if char == '1':
                term.append(f"{var_names[i]}'")
            elif char == '0':
                term.append(var_names[i])
        pos_terms.append("(" + " + ".join(term) + ")" if term else "0")

    final_exp = " ".join(pos_terms) if pos_terms else "1"

    return final_exp, cost_reduction


# Example Use------------------------------------------------------------------
# from lse.core.synthesis.canonical import minterms, maxterms
# minimized_sop, sop_cr = minimize_sop(minterms(module, out), module.inputs)
# minimized_pos, pos_cr = minimize_pos(maxterms(module, out), module.inputs)
# print("Literals Saved: ", sop_cr[1], pos_cr[1])   # cost_reduction = (cubes, literals)
