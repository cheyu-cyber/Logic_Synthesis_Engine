from lse.core.synthesis.literal_minimized import covers, espresso_minimize, expand_cube, minterms_of_cube, to_cubes


def uncovered_pairs(rows, cover):
    """Adjacent rows (one bit apart) that no single cube in cover contains, with their merged cube"""
    pairs = []
    for r in sorted(rows):
        for k, bit in enumerate(r):
            if bit != '0':
                continue
            other = r[:k] + '1' + r[k + 1:]
            if other not in rows:
                continue
            covered = False
            for c in cover:
                if covers(c, r) and covers(c, other):
                    covered = True
                    break
            if not covered:
                pairs.append((r, other, r[:k] + '-' + r[k + 1:]))
    return pairs


def product(cube, names):
    term = ""
    for c, s in zip(cube, names):
        if c == '1':
            term += s
        elif c == '0':
            term += s + "'"
    if term == "":
        return "1"
    return term


def sum_term(cube, names):
    lits = []
    for c, s in zip(cube, names):
        if c == '1':
            lits.append(s + "'")
        elif c == '0':
            lits.append(s)
    return "(" + " + ".join(lits) + ")"


def static_1_hazards(minterms, names):
    """Static-1 hazards of the minimized SOP: [(transition, term to add)]"""
    n = len(names)
    on = to_cubes(minterms, n)
    off = minterms_of_cube('-' * n) - on
    cover = espresso_minimize(on, off)[0]
    hazards = []
    for a, b, m in uncovered_pairs(on, cover):
        transition = f"{product(a, names)} <-> {product(b, names)}"
        fix = product(expand_cube(m, off), names)
        hazards.append((transition, fix))
    return hazards


def static_0_hazards(maxterms, names):
    """Static-0 hazards of the minimized POS: [(transition, sum term to add)]"""
    n = len(names)
    off = to_cubes(maxterms, n)
    on = minterms_of_cube('-' * n) - off
    cover = espresso_minimize(off, on)[0]
    hazards = []
    for a, b, m in uncovered_pairs(off, cover):
        transition = f"{sum_term(a, names)} <-> {sum_term(b, names)}"
        fix = sum_term(expand_cube(m, on), names)
        hazards.append((transition, fix))
    return hazards
