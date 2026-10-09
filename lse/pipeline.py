"""BLIF text -> BlifModule -> regular SOP -> canonical SOP."""
from __future__ import annotations

from lse.core.synthesis.canonical import canonical_sop
from lse.parsers.blif import parse_blif


def run(text: str) -> dict[str, dict[str, str]]:
    """Return {output: {"sop": ..., "canonical_sop": ...}} for each BLIF output."""
    module = parse_blif(text)
    return {out: {"sop": module.nodes[out].to_sop(),
                  "canonical_sop": canonical_sop(module, out)}
            for out in module.outputs}
