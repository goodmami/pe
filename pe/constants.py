
from enum import Enum

# Scan results

NOMATCH = -1

# Processing Operators

class Operators(Enum):
    DEF = 0   # (DEF, name,)
    DOT = 1   # (DOT,)
    LIT = 2   # (LIT, string,)
    CLS = 3   # (CLS, string,)
    SEQ = 4   # (SEQ, exprs,)
    CHC = 5   # (CHC, exprs,)
    RPT = 6   # (RPT, expr, min, max)
    AND = 7   # (AND, expr,)
    NOT = 8   # (NOT, expr,)
    BND = 9   # (BND, name, expr)
    RAW = 10  # (RAW, expr)
