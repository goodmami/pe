
from typing import Tuple, Optional, Any

from pe._errors import Error
from pe._constants import Operator
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
DIS = Operator.DIS
BND = Operator.BND
SEQ = Operator.SEQ
CHC = Operator.CHC
RUL = Operator.RUL


class Definition:
    """An abstract definition of a parsing expression."""
    __slots__ = 'op', 'args',

    def __init__(self, op: Operator, args: Tuple[Any, ...]):
        self.op = op
        self.args = args

    def __repr__(self):
        return f'({self.op}, {self.args!r})'

    def __str__(self):
        return _format(self, 0, None)

    def __eq__(self, other: object):
        if not isinstance(other, Definition):
            return NotImplemented
        return (self.op == other.op) and (self.args == other.args)


def _format(defn: Definition,
            indent: int,
            prev_op: Optional[Operator]) -> str:
    op = defn.op
    args = defn.args
    fmt = '({})' if prev_op and op.precedence >= prev_op.precedence else '{}'
    if op == DOT:
        return '.'
    elif op == LIT:
        return f'"{escape(args[0])}"'
    elif op == CLS:
        return f'[{escape(args[0])}]'
    elif op == RGX:
        raise Error('no syntax exists for regular expressions')
    elif op == SYM:
        return args[0]
    elif op == OPT:
        return fmt.format(_format(args[0], indent, op)) + '?'
    elif op == STR:
        return fmt.format(_format(args[0], indent, op)) + '*'
    elif op == PLS:
        return fmt.format(_format(args[0], indent, op)) + '+'
    elif op == AND:
        return '&' + fmt.format(_format(args[0], indent, op))
    elif op == NOT:
        return '!' + fmt.format(_format(args[0], indent, op))
    elif op == RAW:
        return '~' + fmt.format(_format(args[0], indent, op))
    elif op == DIS:
        return ':' + fmt.format(_format(args[0], indent, op))
    elif op == BND:
        d, name = args
        return f'{name}:' + fmt.format(_format(args[0], indent, op))
    elif op == SEQ:
        return fmt.format(' '.join(_format(d, indent, op)
                                   for d in args[0]))
    elif op == CHC:
        return fmt.format(' / '.join(_format(d, indent, op)
                                     for d in args[0]))
    elif op == RUL:
        raise Error('no syntax exists for rules')
