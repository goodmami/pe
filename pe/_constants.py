
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
    RPT = (_auto(), 5, 'Quantified')   # (RPT, (expr, min, max))
    AND = (_auto(), 4, 'Valued')       # (AND, (expr,))
    NOT = (_auto(), 4, 'Valued')       # (NOT, (expr,))
    CAP = (_auto(), 4, 'Valued')       # (CAP, (expr,))
    BND = (_auto(), 4, 'Valued')       # (BND, (expr, name))
    IGN = (_auto(), 4, 'Valued')       # (IGN, (expr,))
    SEQ = (_auto(), 3, 'Sequential')   # (SEQ, (exprs,))
    RUL = (_auto(), 2, 'Applicative')  # (RUL, (expr, action, name))
    CHC = (_auto(), 1, 'Prioritized')  # (CHC, (exprs,))
    DEF = (_auto(), 0, 'Definitive')   # (DEF, (expr, name))
    DBG = (_auto(), -1, 'Debug')       # (DBG, (expr,))

    @property
    def precedence(self):
        return self.value[1]

    @property
    def type(self):
        return self.value[2]

    def is_unary(self):
        return self.type not in {'Sequential', 'Prioritized'}


class Flag(enum.Flag):
    NONE = 0
    DEBUG = _auto()  # print debugging info for compiled expression
    STRICT = _auto()  # raise error on match failure
    MEMOIZE = _auto()  # use a packrat memo
    INLINE = _auto()  # inline non-recursive rules
    COMMON = _auto()  # replace common idioms with faster alternatives
    REGEX = _auto()  # combine adjacent terms into a single regex
    OPTIMIZE = INLINE | COMMON | REGEX
