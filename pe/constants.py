
from enum import Enum, IntEnum, auto

# Scan results

FAIL = -1  # TODO: Use typing.Final from Python 3.8

# Processing Operators

class Operator(Enum):
    DOT = auto()   # (DOT,)
    LIT = auto()   # (LIT, string,)
    CLS = auto()   # (CLS, chars,)
    RGX = auto()   # (RGX, pattern, flags)
    SEQ = auto()   # (SEQ, exprs,)
    CHC = auto()   # (CHC, exprs,)
    RPT = auto()   # (RPT, expr, min, max,)
    SYM = auto()   # (NAM, name,)
    AND = auto()   # (AND, expr,)
    NOT = auto()   # (NOT, expr,)
    BND = auto()   # (BND, name, expr)
