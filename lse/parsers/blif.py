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

    def value (self, bits):
        hit = any(all(in_table == "-" or int(in_table) == bit for in_table, bit in zip(input_table, bits))
                  for input_table in self.input_table)
        return hit if self.onset else not hit

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
            node.input_table.append("".join(pattern))
            node.onset = bit == "1"
    return module
