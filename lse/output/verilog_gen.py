"""
    Structural Verilog of the minimized SOP.
"""

from lse.core.synthesis.canonical import minterms
from lse.core.synthesis.literal_minimized import espresso_minimize, minterms_of_cube, to_cubes


def generate_verilog(module):
    """Structural Verilog module implementing the minimized SOP of every output"""
    n = len(module.inputs)
    inverted = set()
    wires = []
    body = []

    for out in module.outputs:
        on = to_cubes(minterms(module, out), n)
        cover = sorted(espresso_minimize(on, minterms_of_cube('-' * n) - on)[0])

        # Literal wires of each product term, plus the term as text for the comment
        terms = []
        texts = []
        for cube in cover:
            lits = []
            text = ""
            for c, s in zip(cube, module.inputs):
                if c == '1':
                    lits.append(s)
                    text += s
                elif c == '0':
                    lits.append(s + "_n")
                    text += s + "'"
                    inverted.add(s)
            if text == "":
                text = "1"
            terms.append(lits)
            texts.append(text)
        if texts:
            body.append(f"\n  // {out} = " + " + ".join(texts))
        else:
            body.append(f"\n  // {out} = 0")

        if not cover:                       # constant 0: no gate can drive it, so buf
            body.append(f"  buf ({out}, 1'b0);")
        elif [] in terms:                   # constant 1
            body.append(f"  buf ({out}, 1'b1);")
        elif len(terms) == 1:               # one term
            if len(terms[0]) > 1:           # AND drives the output directly
                body.append(f"  and ({out}, {', '.join(terms[0])});")
            else:                           # one literal
                body.append(f"  buf ({out}, {terms[0][0]});")
        else:
            signals = []
            for k, lits in enumerate(terms):
                if len(lits) == 1:          # single literal: no AND gate needed
                    signals.append(lits[0])
                else:
                    wire = f"{out}_t{k}"
                    wires.append(wire)
                    body.append(f"  and ({wire}, {', '.join(lits)});")
                    signals.append(wire)
            body.append(f"  or ({out}, {', '.join(signals)});")

    # Inverters, in input order
    nots = []
    for s in module.inputs:
        if s in inverted:
            nots.append(s)

    name = module.name
    if not name:
        name = "top"

    lines = []
    lines.append(f"module {name} ({', '.join(module.inputs + module.outputs)});")
    lines.append(f"  input {', '.join(module.inputs)};")
    lines.append(f"  output {', '.join(module.outputs)};")
    declared = []
    for s in nots:
        declared.append(s + "_n")
    for w in wires:
        declared.append(w)
    if declared:
        lines.append(f"  wire {', '.join(declared)};")
    for s in nots:
        lines.append(f"  not ({s}_n, {s});")
    for line in body:
        lines.append(line)
    lines.append("endmodule")
    return "\n".join(lines) + "\n"
