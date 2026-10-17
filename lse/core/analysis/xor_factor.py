"""XOR/XNOR factorization of the minimized SOP.

Two cubes that agree everywhere except two variables x, y, where both values flip,
merge into one term:   P x y' + P x' y = P (x ⊕ y)      P x y + P x' y' = P (x ⊙ y)
"""

from lse.core.synthesis.literal_minimized import espresso_minimize, minterms_of_cube, to_cubes


def xor_pair(c1, c2):
    """(i, j, op) if cubes c1, c2 merge into an XOR/XNOR term on variables i, j, else None"""
    diff = [k for k in range(len(c1)) if c1[k] != c2[k]]
    if len(diff) != 2 or '-' in (c1[diff[0]], c1[diff[1]], c2[diff[0]], c2[diff[1]]):
        return None
    i, j = diff
    return i, j, "⊕" if c1[i] != c1[j] else "⊙"


def term_string(cube, pair, names):
    """Product term of cube, with the pair's two variables written as (x ⊕ y) / (x ⊙ y)"""
    skip = pair[:2] if pair else ()
    lits = [s if c == '1' else s + "'" for k, (c, s) in enumerate(zip(cube, names)) if c != '-' and k not in skip]
    if pair:
        lits.append(f"({names[pair[0]]} {pair[2]} {names[pair[1]]})")
    return "".join(lits) or "1"


def xor_factor(minterms, names):
    """Minimized SOP with XOR/XNOR pairs merged; returns (expression, literals saved vs minimized SOP)"""
    n = len(names)
    on = to_cubes(minterms, n)
    cubes = sorted(espresso_minimize(on, minterms_of_cube('-' * n) - on)[0])

    terms, used = [], set()
    for a in range(len(cubes)):
        for b in range(a + 1, len(cubes)):
            pair = None if used & {a, b} else xor_pair(cubes[a], cubes[b])
            if pair:
                terms.append((cubes[a], pair))
                used |= {a, b}
    terms += [(cubes[a], None) for a in range(len(cubes)) if a not in used]

    saved = sum(len(c) - c.count('-') for c in cubes) - sum(len(c) - c.count('-') for c, _ in terms)
    return " + ".join(term_string(c, p, names) for c, p in terms) or "0", saved
