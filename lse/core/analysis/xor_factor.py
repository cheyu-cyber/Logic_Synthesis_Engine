"""
    XOR/XNOR factorization of the minimized SOP.
    P x y' + P x' y = P (x ⊕ y)      P x y + P x' y' = P (x ⊙ y)
"""

from lse.core.synthesis.literal_minimized import espresso_minimize, minterms_of_cube, to_cubes


def xor_pair(c1, c2):
    """(i, j, op) if cubes c1, c2 merge into an XOR/XNOR term on variables i, j, else None"""
    diff = []
    for k in range(len(c1)):
        if c1[k] != c2[k]:
            diff.append(k)
    if len(diff) != 2:
        return None
    i, j = diff
    if '-' in (c1[i], c1[j], c2[i], c2[j]):
        return None
    if c1[i] != c1[j]:
        return i, j, "⊕"
    return i, j, "⊙"


def term_string(cube, pair, names):
    """Product term of cube, with the pair's two variables written as (x ⊕ y) / (x ⊙ y)"""
    skip = ()
    if pair:
        skip = (pair[0], pair[1])
    term = ""
    for k, (c, s) in enumerate(zip(cube, names)):
        if k in skip:
            continue
        if c == '1':
            term += s
        elif c == '0':
            term += s + "'"
    if pair:
        term += f"({names[pair[0]]} {pair[2]} {names[pair[1]]})"
    if term == "":
        return "1"
    return term


def xor_factor(minterms, names):
    """Minimized SOP with XOR/XNOR pairs merged; returns (expression, literals saved vs minimized SOP)"""
    n = len(names)
    on = to_cubes(minterms, n)
    cubes = sorted(espresso_minimize(on, minterms_of_cube('-' * n) - on)[0])

    # Pair cubes greedily; each cube is used at most once
    terms = []
    used = set()
    for a in range(len(cubes)):
        for b in range(a + 1, len(cubes)):
            if a in used or b in used:
                continue
            pair = xor_pair(cubes[a], cubes[b])
            if pair:
                terms.append((cubes[a], pair))
                used.add(a)
                used.add(b)
    for a in range(len(cubes)):
        if a not in used:
            terms.append((cubes[a], None))

    # Literals saved: fixed bits before minus after (an XOR term keeps its two operands)
    before = 0
    for c in cubes:
        before += len(c) - c.count('-')
    after = 0
    for c, _ in terms:
        after += len(c) - c.count('-')

    texts = []
    for c, p in terms:
        texts.append(term_string(c, p, names))
    if not texts:
        return "0", before - after
    return " + ".join(texts), before - after
