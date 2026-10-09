"""BLIF text -> BlifModule -> regular SOP -> canonical SOP / POS."""
from __future__ import annotations

from lse.core.synthesis.canonical import canonical_pos, canonical_sop, maxterms, minterms
from lse.parsers.blif import parse_blif


def run(text: str) -> dict[str, dict]:
    module = parse_blif(text)
    return {out: {"sop": module.nodes[out].to_sop(),
                  "minterms": minterms(module, out),
                  "canonical_sop": canonical_sop(module, out),
                  "maxterms": maxterms(module, out),
                  "canonical_pos": canonical_pos(module, out)}
            for out in module.outputs}
