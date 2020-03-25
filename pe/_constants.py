
import enum

_auto = enum.auto

# Basic constants

FAIL = -1  # TODO: Use typing.Final from Python 3.8

ANONYMOUS = '<anonymous>'  # name for unnamed rules

MAX_MEMO_SIZE = 1000  # simultaneous cacheable string positions
DEL_MEMO_SIZE = 500   # positions to clear when limit is reached


# Processing Operators

class Operator(enum.Enum):
    DOT = _auto()  # (DOT, ())
    LIT = _auto()  # (LIT, (string,))
    CLS = _auto()  # (CLS, (chars,))
    RGX = _auto()  # (RGX, (pattern, flags))
    SYM = _auto()  # (SYM, (name,))
    OPT = _auto()  # (OPT, (expr,))
    STR = _auto()  # (STR, (expr,))
    PLS = _auto()  # (PLS, (expr,))
    AND = _auto()  # (AND, (expr,))
    NOT = _auto()  # (NOT, (expr,))
    RAW = _auto()  # (RAW, (expr,))
    DIS = _auto()  # (DIS, (expr,))
    BND = _auto()  # (BND, (expr, name))
    SEQ = _auto()  # (SEQ, (exprs,))
    CHC = _auto()  # (CHC, (exprs,))
    RUL = _auto()  # (RUL, (expr, action, name))


class Value(enum.Enum):
    EMPTY    = 'empty'
    ATOMIC   = 'atomic'
    ITERABLE = 'iterable'
    DEFERRED = 'deferred'


class Flag(enum.Flag):
    NONE     = 0
    DEBUG    = _auto()  # print debugging info for compiled expression
    STRICT   = _auto()  # raise error on match failure
    MEMOIZE  = _auto()  # use a packrat memo
    INLINE   = _auto()  # inline non-recursive rules
    MERGE    = _auto()  # merge adjacent terms if possible
    REGEX    = _auto()  # combine adjacent terms into a single regex
    OPTIMIZE = INLINE | REGEX # | MERGE disabled while behavior differs
