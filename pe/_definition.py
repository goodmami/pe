
from typing import Dict, Tuple, Callable, Any

from pe._constants import Operator
from pe._errors import Error
from pe._escape import escape


DOT = Operator.DOT
LIT = Operator.LIT
CLS = Operator.CLS
RGX = Operator.RGX
SYM = Operator.SYM
OPT = Operator.OPT
STR = Operator.STR
RPT = Operator.RPT
PLS = Operator.PLS
AND = Operator.AND
NOT = Operator.NOT
CAP = Operator.CAP
BND = Operator.BND
SEQ = Operator.SEQ
IGN = Operator.IGN
CHC = Operator.CHC
RUL = Operator.RUL
DEF = Operator.DEF
DBG = Operator.DBG


class Definition:
    """An abstract definition of a parsing expression."""
    __slots__ = 'op', 'args',

    def __init__(self, op: Operator, args: Tuple[Any, ...]):
        self.op = op
        self.args = args

    def __repr__(self):
        return f'({self.op}, {self.args!r})'

    def __str__(self):
        return _format(self, None)

    def __eq__(self, other: object):
        if not isinstance(other, Definition):
            return NotImplemented
        return (self.op == other.op
                and self.args == other.args)

    def format(self) -> str:
        return _format(self, DEF)


def _format_dot(defn: Definition, prev_op: Operator) -> str:
    return '.'


def _format_literal(defn: Definition, prev_op: Operator) -> str:
    return f'''"{escape(defn.args[0], ignore="'[]")}"'''


def _format_class(defn: Definition, prev_op: Operator) -> str:

    def esc(s):
        return escape(s, ignore='"\'')

    clsstr = ''.join(f'{esc(a)}-{esc(b)}' if b else esc(a)
                     for a, b in defn.args[0])
    if defn.args[1]:
        return f'''(![{clsstr}] .)'''
    else:
        return f'''[{clsstr}]'''


def _format_regex(defn: Definition, prev_op: Operator) -> str:
    return f'`{defn.args[0]}`'  # temporary syntax


def _format_nonterminal(defn: Definition, prev_op: Operator) -> str:
    return defn.args[0]


def _format_repetition(defn: Definition, prev_op: Operator) -> str:
    print('rec', defn.op, prev_op)
    subdef, _min, _max = defn.args
    if _min == _max:
        body = str(_min)
    else:
        body = f"{'' if _min == 0 else _min},{'' if _max == -1 else _max}"
    return f"{_format(subdef, defn.op)}{{{body}}}"


_format_decorators: Dict[Operator, Tuple[str, str, str]] = {
    # OP: (prefix, delim, suffix)
    OPT: ('', '', '?'),
    STR: ('', '', '*'),
    PLS: ('', '', '+'),
    RPT: ('', '', ''),
    AND: ('&', '', ''),
    NOT: ('!', '', ''),
    CAP: ('~', '', ''),
    BND: ('{}:', '', ''),
    SEQ: ('', ' ', ''),
    IGN: ('<', '', ''),
    CHC: ('', ' / ', ''),
    RUL: ('', '', '  -> {}'),
}


def _format_recursive(defn: Definition, prev_op: Operator) -> str:
    op = defn.op
    args = defn.args
    prefix, delimiter, suffix = _format_decorators[op]
    fmt = '({})' if prev_op and op.precedence <= prev_op.precedence else '{}'
    if delimiter:
        body = delimiter.join(_format(d, op) for d in args[0])
    else:
        body = _format(args[0], op)
    body = body.replace('{', '{{').replace('}', '}}')
    return fmt.format((prefix + body + suffix).format(*args[1:]))


def _format_debug(defn: Definition, prev_op: Operator) -> str:
    return _format(defn.args[0], prev_op)


_Formatter = Callable[[Definition, Operator], str]


_format_map: Dict[Operator, _Formatter] = {
    DOT: _format_dot,
    LIT: _format_literal,
    CLS: _format_class,
    RGX: _format_regex,
    SYM: _format_nonterminal,
    OPT: _format_recursive,
    STR: _format_recursive,
    PLS: _format_recursive,
    RPT: _format_repetition,
    AND: _format_recursive,
    NOT: _format_recursive,
    CAP: _format_recursive,
    BND: _format_recursive,
    SEQ: _format_recursive,
    IGN: _format_recursive,
    CHC: _format_recursive,
    RUL: _format_recursive,
    DBG: _format_debug,
}


def _format(defn: Definition,
            prev_op: Operator) -> str:
    op = defn.op
    if op in _format_map:
        return _format_map[op](defn, prev_op)
    else:
        raise Error(f'invalid operation: {defn.op!r}')
