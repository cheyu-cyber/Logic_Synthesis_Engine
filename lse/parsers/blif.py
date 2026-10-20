from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

@dataclass
class BlifNodes:

    name: str
    output: str
    inputs: list[str]
    input_table: list[str] = field(default_factory=list)
    onset: bool = True
    off_table: list[str] = field(default_factory=list)     # rows ending in 0 (OFF-set), see resolve_covers

    def value(self, bits):
        """Output of this node for the given input bits (one per name in self.inputs)."""
        hit = False                         # does any row of the cover match the inputs?
        for row in self.input_table:
            match = True
            for c, bit in zip(row, bits):
                if c != "-" and int(c) != bit:
                    match = False
                    break
            if match:
                hit = True
                break
        if self.onset:
            return hit                      # rows list the ON-set: a match means 1
        return not hit                      # rows list the OFF-set: a match means 0

    def to_sop(self):
        """Compute the regular SOP form of a cover, e.g. "ab' + c"."""
        input = self.inputs
        terms = []
        for input_table in self.input_table:
            term = "".join(s if c == "1" else s + "'" for c, s in zip(input_table, input)
               if c != "-") or "1"
            terms.append(term)
        sop = "1" if "1" in terms else " + ".join(terms) or "0"
        if self.onset:
            return sop
        return {"0": "1", "1": "0"}.get(sop, f"({sop})'")

@dataclass
class BlifModule:
    
    name: str
    inputs: list[str]
    outputs: list[str]
    nodes: dict[str, BlifNodes] = field(default_factory=dict)

    def evaluate(self, values):
        env = {s: int(values[s]) for s in self.inputs}
        return {o: self._value(o, env) for o in self.outputs}
 
    def _value(self, sig, env):
        if sig not in env:
            env[sig] = None                      # "being computed", to catch loops
            node = self.nodes[sig]
            env[sig] = node.value([self._value(s, env) for s in node.inputs])
        return env[sig]

def parse_blif(text: str) -> BlifModule:
    """Parse BLIF text into a BlifModule."""
    module = BlifModule(name="", inputs=[], outputs=[])
    node = None
    for raw in text.replace("\\\n", " ").splitlines():
        tokens = raw.split("#", 1)[0].split()
        if not tokens:
            continue
        key = tokens[0]
        if key == ".model":
            module.name = " ".join(tokens[1:])
        elif key == ".inputs":
            module.inputs += tokens[1:]
        elif key == ".outputs":
            module.outputs += tokens[1:]
        elif key == ".names":
            *ins, out = tokens[1:]
            node = module.nodes[out] = BlifNodes(name=out, output=out, inputs=ins)
        elif key == ".end":
            break
        elif key.startswith("."):
            raise ValueError(f"unsupported BLIF directive: {key}")
        elif node is None:
            raise ValueError(f"cover row outside .names: {raw.strip()}")
        else:
            *pattern, bit = tokens
            if bit == "1":
                node.input_table.append("".join(pattern))
            elif bit == "0":
                node.off_table.append("".join(pattern))
            else:
                raise ValueError(f".names {node.output}: output value must be 0 or 1: {raw.strip()}")
    resolve_covers(module)
    return module


def overlaps(row1, row2):
    """True if two cover rows share an input combination (no position is 0 in one and 1 in the other)"""
    for a, b in zip(row1, row2):
        if (a == "0" and b == "1") or (a == "1" and b == "0"):
            return False
    return True


def resolve_covers(module):
    """1 rows give the ON-set, 0 rows the OFF-set (BLIF spec). A cover with only 0 rows describes F';
    in a mixed cover the 1 rows define F (unlisted rows are 0) and no 0 row may overlap a 1 row."""
    for node in module.nodes.values():
        if node.off_table and not node.input_table:
            node.input_table, node.off_table = node.off_table, []
            node.onset = False
        else:
            for off in node.off_table:
                for on in node.input_table:
                    if overlaps(on, off):
                        raise ValueError(f".names {node.output}: rows '{on} 1' and '{off} 0' overlap")
