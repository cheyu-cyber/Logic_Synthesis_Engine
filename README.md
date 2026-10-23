# Logic_Synthesis_Engine

## Usage
python -m lse.cli

python -m lse.cli examples/full_adder.blif 

python -m lse.cli examples/full_adder.blif > output_log/full_adder.txt

## Goal
Input: file (EDA standards) read via cli interface/gui with standard file picker.

Input requirements: A boolean algebraic function with SOP / POS (optional) support.

Process: 
1. Compute Forward and inverse Canonical SOP/POS and display.
2. Literal Minimized SOP/POS with metrics on literals saved.
3. Report Prime Implicants, Essentional Prime Implicants, On-Set Minterms, Off-set Maxterms count/number
4. Hazard Detection, Delay estimation, XOR/XNOR factorization

Output:
1. Output text results
2. Display Process 1 and 2, 3(metrics), 4(decide at least 2)
3. output a gate level modeling verilog file (.v) with minimized circuit
