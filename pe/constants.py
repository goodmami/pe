
import enum

_auto = enum.auto

# Scan results

FAIL = -1  # TODO: Use typing.Final from Python 3.8

# Processing Operators

class Operator(enum.Enum):
    DOT = _auto()  # (DOT, ())
    LIT = _auto()  # (LIT, (string,))
    CLS = _auto()  # (CLS, (chars,))
    RGX = _auto()  # (RGX, (pattern, flags))
    SYM = _auto()  # (SYM, (name,))
    OPT = _auto()  # (OPT, (expr,))
    RPT = _auto()  # (RPT, (expr, min, max,))
    AND = _auto()  # (AND, (expr,))
    NOT = _auto()  # (NOT, (expr,))
    BND = _auto()  # (BND, (name, expr))
    SEQ = _auto()  # (SEQ, (exprs,))
    CHC = _auto()  # (CHC, (exprs,))
    RUL = _auto()  # (RUL, (expr, action))


class ValueType(enum.Enum):
    NILADIC = 'niladic'
    MONADIC = 'monadic'
    VARIADIC = 'variadic'
    DEFERRED = 'deferred'


class Flag(enum.Flag):
    NONE = 0
    DEBUG = _auto()    # print debugging info for compiled expression
    STRICT = _auto()   # raise error on match failure
    MEMOIZE = _auto()  # use a packrat memo
    INLINE = _auto()   # inline non-recursive rules
    MERGE = _auto()    # merge adjacent terms if possible
    REGEX = _auto()    # combine adjacent terms into a single regex
    OPTIMIZE = INLINE | MERGE | REGEX
