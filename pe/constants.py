
from enum import Enum, IntEnum, auto

# Scan results

FAIL = -1  # TODO: Use typing.Final from Python 3.8

# Processing Operators

class Operator(Enum):
    DOT = auto()   # (DOT, ())
    LIT = auto()   # (LIT, (string,))
    CLS = auto()   # (CLS, (chars,))
    RGX = auto()   # (RGX, (pattern, flags))
    SYM = auto()   # (SYM, (name,))
    OPT = auto()   # (OPT, (expr,))
    RPT = auto()   # (RPT, (expr, min, max,))
    AND = auto()   # (AND, (expr,))
    NOT = auto()   # (NOT, (expr,))
    BND = auto()   # (BND, (name, expr))
    RAW = auto()   # (RAW, (expr))
    SEQ = auto()   # (SEQ, (exprs,))
    CHC = auto()   # (CHC, (exprs,))
