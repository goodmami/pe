
from typing import Dict, Tuple, Callable, Any

from pe._constants import Operator, Value
from pe._errors import Error
from pe._escape import escape


DOT = Operator.DOT
LIT = Operator.LIT
CLS = Operator.CLS
RGX = Operator.RGX
SYM = Operator.SYM
OPT = Operator.OPT
STR = Operator.STR
PLS = Operator.PLS
AND = Operator.AND
NOT = Operator.NOT
RAW = Operator.RAW
BND = Operator.BND
SEQ = Operator.SEQ
CHC = Operator.CHC
RUL = Operator.RUL
DEF = Operator.DEF


class Definition:
    """An abstract definition of a parsing expression."""
    __slots__ = 'op', 'args', 'value',

    def __init__(self, op: Operator, args: Tuple[Any, ...], value: Value):
        self.op = op
        self.args = args
        self.value = value

    def __repr__(self):
        return f'({self.op}, {self.args!r}, {self.value!r})'

    def __str__(self):
        return _format(self, None)

    def __eq__(self, other: object):
        if not isinstance(other, Definition):
            return NotImplemented
        return (self.op == other.op
                and self.args == other.args
                and self.value == other.value)

    def format(self) -> str:
        return _format(self, DEF)


def _format_dot(defn: Definition, prev_op: Operator) -> str:
    return '.'


def _format_literal(defn: Definition, prev_op: Operator) -> str:
    return f'''"{escape(defn.args[0], ignore="'-[]")}"'''


def _format_class(defn: Definition, prev_op: Operator) -> str:
    # TODO: properly escape classes
    return f'[{defn.args[0]}]'


def _format_regex(defn: Definition, prev_op: Operator) -> str:
    return f'`{defn.args[0]}`'  # temporary syntax


def _format_nonterminal(defn: Definition, prev_op: Operator) -> str:
    return defn.args[0]


_format_decorators: Dict[Operator, Tuple[str, str, str]] = {
    OPT: ('', '', '?'),
    STR: ('', '', '*'),
    PLS: ('', '', '+'),
    AND: ('&', '', ''),
    NOT: ('!', '', ''),
    RAW: ('~', '', ''),
    BND: ('{}:', '', ''),
    SEQ: ('', ' ', ''),
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
    return fmt.format((prefix + body + suffix).format(*args[1:]))


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
    AND: _format_recursive,
    NOT: _format_recursive,
    RAW: _format_recursive,
    BND: _format_recursive,
    SEQ: _format_recursive,
    CHC: _format_recursive,
    RUL: _format_recursive,
}


def _format(defn: Definition,
            prev_op: Operator) -> str:
    try:
        func = _format_map[defn.op]
    except KeyError:
        raise Error('inalid operation: {op!r}')
    return func(defn, prev_op)
