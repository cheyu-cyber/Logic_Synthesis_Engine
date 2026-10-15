"""Forward and inverse Canonical SOP and POS forms synthesis module."""

from __future__ import annotations
from lse.parsers.blif import BlifModule


def minterms(module: BlifModule, output):
    n = len(module.inputs)
    result = []
    for m in range(2 ** n):
        values = {}
        for i, s in enumerate(module.inputs):
            values[s] = (m >> (n - 1 - i)) & 1    # bit i of m, first input as the MSB
        if module._value(output, values):
            result.append(m)
    return result

def maxterms(module: BlifModule, output):
    n = len(module.inputs)
    result = []
    for m in range(2 ** n):
        values = {}
        for i, s in enumerate(module.inputs):
            values[s] = (m >> (n - 1 - i)) & 1    # bit i of m, first input as the MSB
        if not module._value(output, values):
            result.append(m)
    return result

def canonical_sop(module: BlifModule, output):
    """Output sum of minterms"""
    n = len(module.inputs)
    terms = []
    for m in minterms(module, output):
        literals = []
        for i, s in enumerate(module.inputs):
            if (m >> (n - 1 - i)) & 1:
                literals.append(s)
            else:
                literals.append(s + "'")
        terms.append("".join(literals) or "1")    # no inputs: the minterm is just 1
    if not terms:
        return "0"
    return " + ".join(terms)

def canonical_pos(module: BlifModule, output):
    """Output product of maxterms"""
    n = len(module.inputs)
    terms = []
    for m in maxterms(module, output):
        literals = []
        for i, s in enumerate(module.inputs):
            if (m >> (n - 1 - i)) & 1:
                literals.append(s + "'")
            else:
                literals.append(s)
        terms.append("(" + " + ".join(literals) + ")" if literals else "0")    # no inputs: the maxterm is just 0
    if not terms:
        return "1"
    return " ".join(terms)

def inverse_canonical_sop(module: BlifModule, output):
    """Output inverse as sum of minterms (minterms of F' are the maxterms of F)"""
    n = len(module.inputs)
    terms = []
    for m in maxterms(module, output):
        literals = []
        for i, s in enumerate(module.inputs):
            if (m >> (n - 1 - i)) & 1:
                literals.append(s)
            else:
                literals.append(s + "'")
        terms.append("".join(literals) or "1")    # no inputs: the minterm is just 1
    if not terms:
        return "0"
    return " + ".join(terms)

def inverse_canonical_pos(module: BlifModule, output):
    """Output inverse as product of maxterms (maxterms of F' are the minterms of F)"""
    n = len(module.inputs)
    terms = []
    for m in minterms(module, output):
        literals = []
        for i, s in enumerate(module.inputs):
            if (m >> (n - 1 - i)) & 1:
                literals.append(s + "'")
            else:
                literals.append(s)
        terms.append("(" + " + ".join(literals) + ")" if literals else "0")    # no inputs: the maxterm is just 0
    if not terms:
        return "1"
    return " ".join(terms)
