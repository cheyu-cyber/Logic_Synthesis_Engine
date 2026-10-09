"""Forward and inverse Canonical SOP and POS forms synthesis module."""

from __future__ import annotations
from lse.parsers.blif import BlifModule


def minterms(module: BlifModule, output):
    n = len(module.inputs)
    return [m for m in range(2 ** n)
            if module._value(output, {s: m >> (n - 1 - i) & 1 for i, s in enumerate(module.inputs)})]

def canonical_sop(module: BlifModule, output):
    """The output as a sum of minterms"""
    n = len(module.inputs)
    terms = ["".join(s if m >> (n - 1 - i) & 1 else s + "'" for i, s in enumerate(module.inputs))
                for m in minterms(module, output)]
    if not terms:
        return "0"
    return " + ".join(terms) or "1"

 