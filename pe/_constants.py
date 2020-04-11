
import enum

_auto = enum.auto

# Basic constants

FAIL = -1  # TODO: Use typing.Final from Python 3.8

ANONYMOUS = '<anonymous>'  # name for unnamed rules

MAX_MEMO_SIZE = 500  # simultaneous cacheable string positions
DEL_MEMO_SIZE = 200  # positions to clear when limit is reached


# Processing Operators

class Operator(enum.Enum):
    DOT = (_auto(), 6, 'Primary')      # (DOT, ())
    LIT = (_auto(), 6, 'Primary')      # (LIT, (string,))
    CLS = (_auto(), 6, 'Primary')      # (CLS, (chars,))
    RGX = (_auto(), 6, 'Primary')      # (RGX, (pattern, flags))
    SYM = (_auto(), 6, 'Primary')      # (SYM, (name,))
    OPT = (_auto(), 5, 'Quantified')   # (OPT, (expr,))
    STR = (_auto(), 5, 'Quantified')   # (STR, (expr,))
    PLS = (_auto(), 5, 'Quantified')   # (PLS, (expr,))
    AND = (_auto(), 4, 'Valued')       # (AND, (expr,))
    NOT = (_auto(), 4, 'Valued')       # (NOT, (expr,))
    RAW = (_auto(), 4, 'Valued')       # (RAW, (expr,))
    BND = (_auto(), 4, 'Valued')       # (BND, (expr, name))
    SEQ = (_auto(), 3, 'Sequential')   # (SEQ, (exprs,))
    RUL = (_auto(), 2, 'Applicative')  # (RUL, (expr, action, name))
    CHC = (_auto(), 1, 'Prioritized')  # (CHC, (exprs,))

    @property
    def precedence(self):
        return self.value[1]

    @property
    def type(self):
        return self.value[2]


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
