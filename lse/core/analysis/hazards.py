from lse.core.synthesis.literal_minimized import covers, espresso_minimize, expand_cube, minterms_of_cube, to_cubes


def uncovered_pairs(rows, cover):
    """Adjacent rows (one bit apart) that no single cube in cover contains, with their merged cube"""
    pairs = []
    for r in sorted(rows):
        for k, bit in enumerate(r):
            other = r[:k] + '1' + r[k + 1:]
            if bit == '0' and other in rows and not any(covers(c, r) and covers(c, other) for c in cover):
                pairs.append((r, other, r[:k] + '-' + r[k + 1:]))
    return pairs


def product(cube, names):
    return "".join(s if c == '1' else s + "'" for c, s in zip(cube, names) if c != '-') or "1"


def sum_term(cube, names):
    return "(" + " + ".join(s + "'" if c == '1' else s for c, s in zip(cube, names) if c != '-') + ")"


def static_1_hazards(minterms, names):
    """Static-1 hazards of the minimized SOP: [(transition, term to add)]"""
    n = len(names)
    on = to_cubes(minterms, n)
    off = minterms_of_cube('-' * n) - on
    cover = espresso_minimize(on, off)[0]
    return [(f"{product(a, names)} <-> {product(b, names)}", product(expand_cube(m, off), names))
            for a, b, m in uncovered_pairs(on, cover)]


def static_0_hazards(maxterms, names):
    """Static-0 hazards of the minimized POS: [(transition, sum term to add)]"""
    n = len(names)
    off = to_cubes(maxterms, n)
    on = minterms_of_cube('-' * n) - off
    cover = espresso_minimize(off, on)[0]
    return [(f"{sum_term(a, names)} <-> {sum_term(b, names)}", sum_term(expand_cube(m, on), names))
            for a, b, m in uncovered_pairs(off, cover)]
