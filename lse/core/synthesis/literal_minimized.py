"""Literal Minimized SOP/POSforms synthesis module.
Using Quine-McCluskey, Espresso-like, or K-map minimization
"""

import re

# this submodule will take in the boolean expression from
# the user and simplify it before moving on to logic synthesis


def clean_expression(input_str: str, chars: str = " \t\n\r'\"") -> str:
    """
    Removes leading and trailing whitespace, quotes, and specified characters
    from the input string.
    """
    return input_str.strip(chars)


# replaces invalid but recognizable aspects of potential inputs
def normalize_input(expr_str: str):
    """
    Normalizes boolean keywords, parses the expression into a SymPy object,
    and extracts all unique SymPy Symbol objects present in the expression.

    Returns:
        tuple: (sympy_expression, sorted_list_of_symbols)
    """
    # Replace common text-based boolean operators
    # with SymPy-compatible operators
    replacements = {
        "AND": "&",
        "OR": "|",
        "NOT": "~",
        "XOR": "^",
        "and": "&",
        "or": "|",
        "not": "~",
        "xor": "^"
    }
    # Simple word replacement using regex for accurate token boundary matching
    for word, op in replacements.items():
        normalized_str = re.sub(rf'\b{word}\b', op, expr_str)

    return normalized_str


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

    return F, cost_reduction, F_exp


# =====================================================================
# WRAPPER & HELPER FUNCTIONS
# =====================================================================
def minimize_sop_string(sop_str, var_names):
    """Minimizes an SOP string expression (e.g. "A'B'C + A'BC + AB'C")."""

    print("----Minimizing SOP expression with Espresso Algorithm----")

    raw_terms = [t.strip() for t in sop_str.split('+')]
    print("raw terms:", raw_terms)
    num_vars = len(var_names)

    # 1. Map input terms to positional binary cubes
    F_init = set()
    for term in raw_terms:
        pattern = []
        for var in var_names:
            if var + "'" in term:
                pattern.append('0')
            elif var in term:
                pattern.append('1')
            else:
                pattern.append('-')
        F_init.add("".join(pattern))

    # 2. Compute ON-set minterms and generate OFF-set (R)
    on_minterms = set().union(*(minterms_of_cube(c) for c in F_init))
    print("on_minterms:", on_minterms)
    all_minterms = {format(i, f'0{num_vars}b') for i in range(1 << num_vars)}
    R_off = all_minterms - on_minterms

    # 3. Run Espresso algorithm
    optimized_cubes, cost_reduction, prime_imps = espresso_minimize(F_init,
                                                                    R_off)

    # 4. Convert output cubes back to Boolean algebraic string
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

    return final_exp, cost_reduction, prime_imps


def minimize_pos_string(pos_str, var_names):
    """Minimizes an POS string expression (e.g. "A'+B'+C * A'+B+C)."""

    print("----Minimizing POS expression with Espresso Algorithm----")

    raw_terms = [t.strip() for t in pos_str.split('*')]
    num_vars = len(var_names)

    # 1. Map input terms to positional binary cubes
    F_off = set()
    for term in raw_terms:
        pattern = []
        for var in var_names:
            if var + "'" in term:
                pattern.append('0')
            elif var in term:
                pattern.append('1')
            else:
                pattern.append('-')
        F_off.add("".join(pattern))

    # 2. Compute ON-set minterms and generate OFF-set (R)
    off_minterms = set().union(*(minterms_of_cube(c) for c in F_off))
    all_minterms = {format(i, f'0{num_vars}b') for i in range(1 << num_vars)}

    # F_init_off_set = all_minterms - on_minterms
    R_on = all_minterms - off_minterms

    # 3. Run Espresso algorithm
    optimized_cubes, cost_reduction, prime_imps = espresso_minimize(F_off,
                                                                    R_on)

    # 4. Convert output cubes back to Boolean algebraic string
    pos_terms = []
    for c in sorted(optimized_cubes):
        term = []
        for i, char in enumerate(c):
            if char == '1':
                term.append(var_names[i])
            elif char == '0':
                term.append(f"{var_names[i]}'")

        pos_terms.append("(" + " + ".join(term) + ")")

    final_exp = " * ".join(pos_terms)

    return final_exp, cost_reduction, prime_imps


# Example Use: Unminimized SOP Expression-------------------------------------
var_names = ['A', 'B', 'C']
# sop_input = "A'B'C'D' + A'B'CD' + A'BC'D + A'BCD + AB'C'D' + AB'CD' + ABCD"
# # correct result: B'D' + BCD + A'BD

sop_input = "A'B'C + A'BC + AB'C + ABC"
# correct result: C

minimized_sop, cost_reduction, prime_imps = minimize_sop_string(sop_input,
                                                                var_names)

print("\nOriginal Expression: ", sop_input)
print("\nEspresso Minimization: ", minimized_sop)
print("\nPrime Implicants: ", prime_imps)

print("\nCost Reduction:")
# cubes_reduced = cost_reduction[0]
# print("Cubes Reduced: ", cubes_reduced)
literals_reduced = cost_reduction[1]
print("Literals Reduced: ", literals_reduced)


# Example Use: Unminimized POS Expression-------------------------------------
# var_names = ['A', 'B', 'C']
# pos_input = "(A+B+C')*(A+B'+C')*(A'+B'+C')*(A'+B+C)*(A+B+C)"
# # correct result: (B+C) * (B'+C') * (A+C')

var_names = ['A', 'B', 'C', 'D']
pos_input = "(A'+B'+C+D)*(A'+B'+C'+D)*(A'+B'+C'+D')*(A'+B+C+D)*(A+B'+C'+D)*(A+B'+C'+D')*(A+B+C+D)*(A'+B'+C+D')"
# correct result: (B+C+D) * (A'+B') * (B'+C')

minimized_pos, cost_reduction, prime_imps = minimize_pos_string(pos_input,
                                                                var_names)

print("\nOriginal Expression: ", pos_input)
print("\nEspresso Minimization: ", minimized_pos)
print("\nPrime Implicants: ", prime_imps)

print("\nCost Reduction:")
# cubes_reduced = cost_reduction[0]
# print("Cubes Reduced: ", cubes_reduced)
literals_reduced = cost_reduction[1]
print("Literals Reduced: ", literals_reduced)
