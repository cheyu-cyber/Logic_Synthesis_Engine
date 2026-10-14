"""BLIF text -> BlifModule -> regular SOP -> canonical SOP / POS."""
from __future__ import annotations

from lse.core.synthesis.canonical import canonical_pos, canonical_sop, maxterms, minterms
from lse.core.synthesis.literal_minimized import minimize_sop_string, minimize_pos_string
from lse.core.synthesis.implicants import get_pi, get_epi
from lse.parsers.blif import parse_blif


def run(text: str) -> dict[str, dict]:
    module = parse_blif(text)
    results = {}

    for out in module.outputs:
        c_sop = canonical_sop(module, out)
        minimized_sop, sop_cr = minimize_sop_string(canonical_sop)
        c_pos = canonical_pos(module, out)
        minimized_pos, pos_cr = minimize_pos_string(canonical_pos)
        prime_imps = get_pi(c_sop)
        essential_pis = get_epi(prime_imps)
        results[out] = {"sop": module.nodes[out].to_sop(),
                        "minterms": minterms(module, out),
                        "canonical_sop": c_sop,
                        "maxterms": maxterms(module, out),
                        "canonical_pos": c_pos,
                        "minimized_sop": minimized_sop,
                        "sop_cost_reduction": sop_cr,
                        "minimized_pos": minimized_pos,
                        "pos_cost_reduction": pos_cr,
                        "pi_count": len(prime_imps),
                        "epi_count": len(essential_pis)
                        }

    return results
