"""BLIF text -> BlifModule -> canonical / inverse canonical SOP & POS -> minimized SOP & POS -> (E)PIs."""
from __future__ import annotations

from lse.core.synthesis.canonical import (canonical_pos, canonical_sop, inverse_canonical_pos,
                                          inverse_canonical_sop, maxterms, minterms)
from lse.core.synthesis.literal_minimized import minimize_sop, minimize_pos
from lse.core.synthesis.implicants import get_pi, get_epi
from lse.parsers.blif import parse_blif


def run(text: str) -> dict[str, dict]:
    module = parse_blif(text)
    results = {}

    for out in module.outputs:
        mins = minterms(module, out)
        maxs = maxterms(module, out)
        minimized_sop, sop_cr = minimize_sop(mins, module.inputs)
        minimized_pos, pos_cr = minimize_pos(maxs, module.inputs)
        prime_imps = get_pi(mins, module.inputs)
        essential_pis = get_epi(prime_imps, mins, module.inputs)
        results[out] = {"sop": module.nodes[out].to_sop(),
                        "minterms": mins,
                        "canonical_sop": canonical_sop(module, out),
                        "maxterms": maxs,
                        "canonical_pos": canonical_pos(module, out),
                        "inverse_canonical_sop": inverse_canonical_sop(module, out),
                        "inverse_canonical_pos": inverse_canonical_pos(module, out),
                        "minimized_sop": minimized_sop,
                        "sop_cost_reduction": sop_cr,
                        "minimized_pos": minimized_pos,
                        "pos_cost_reduction": pos_cr,
                        "pi_count": len(prime_imps),
                        "epi_count": len(essential_pis)
                        }

    return results
