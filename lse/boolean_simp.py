import sympy as sp
import re

# this submodule will take in the boolean expression from
# the user and simplify it before moving on to logic synthesis

# remove leading and trailing characters
def clean_expression(input_str: str, chars: str = " \t\n\r'\"") -> str:
    """
    Removes leading and trailing whitespace, quotes, and specified characters 
    from the input string.
    """
    return input_str.strip(chars)


# identify symbols
def logic_simplify(expr_str: str):
    """
    Normalizes boolean keywords, parses the expression into a SymPy object,
    and extracts all unique SymPy Symbol objects present in the expression.
    
    Returns:
        tuple: (sympy_expression, sorted_list_of_symbols)
    """
    # Replace common text-based boolean operators with SymPy-compatible operators
    replacements = {
        "AND": "&",
        "OR": "|",
        "NOT": "~",
        "XOR": "^",
        "and": "&",
        "or": "|",
        "not": "~",
        "xor": "^"
    }


    # Simple word replacement using regex for accurate token boundary matching
    for word, op in replacements.items():
        normalized_str = re.sub(rf'\b{word}\b', op, expr_str)
    
    # Extract unique free symbols as a sorted list
    # symbols = sorted(list(normalized_str.free_symbols), key=lambda s: s.name)

    simplified_expr = sp.simplify_logic(normalized_str)
    
    return simplified_expr

# # example use:
# final_expr = logic_simplify(clean_expression('(notA and notB and C) or (notA and B and C) or (A*~B*C) + (A*B*C)'))

# # output: C

