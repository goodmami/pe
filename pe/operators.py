

from typing import Union, Tuple, Dict, Pattern, Callable, Any

from pe._constants import Operator
from pe._core import Error


class Definition:
    """An abstract definition of a parsing expression."""
    __slots__ = 'op', 'args',

    def __init__(self, op: Operator, args: Tuple[Any, ...]):
        self.op = op
        self.args = args

    def __repr__(self):
        return f'({self.op}, {self.args!r})'

    def __eq__(self, other: 'Definition'):
        return (self.op == other.op) and (self.args == other.args)


_Defn = Union[str, Definition]


def _validate(arg: _Defn):
    if isinstance(arg, str):
        return Literal(arg)
    elif not isinstance(arg, Definition):
        raise ValueError(f'not a valid definition: {arg!r}')
    elif not isinstance(arg.op, Operator):
        raise ValueError(f'not a valid operator: {arg.op!r}')
    else:
        return arg


def Dot():
    return Definition(Operator.DOT, ())


def Literal(string: str):
    return Definition(Operator.LIT, (string,))


def Class(chars: str):
    return Definition(Operator.CLS, (chars,))


def Regex(pattern: Union[str, Pattern], flags: int = 0):
    return Definition(Operator.RGX, (pattern, flags))


def Sequence(*expressions: _Defn):
    exprs = list(map(_validate, expressions))
    if len(exprs) == 1:
        return exprs[0]
    else:
        _exprs = []
        for expr in exprs:
            if expr.op == Operator.SEQ:
                _exprs.extend(expr.args[0])
            else:
                _exprs.append(expr)
        return Definition(Operator.SEQ, (_exprs,))


def Choice(*expressions: _Defn):
    exprs = list(map(_validate, expressions))
    if len(exprs) == 1:
        return exprs[0]
    else:
        _exprs = []
        for expr in exprs:
            if expr.op == Operator.CHC:
                _exprs.extend(expr.args[0])
            else:
                _exprs.append(expr)
        return Definition(Operator.CHC, (_exprs,))


def Optional(expression: _Defn):
    return Definition(Operator.OPT, (_validate(expression),))


def Star(expression: _Defn):
    return Definition(Operator.STR, (_validate(expression),))


def Plus(expression: _Defn):
    return Definition(Operator.PLS, (_validate(expression),))


def Nonterminal(name: str):
    return Definition(Operator.SYM, (name,))


def And(expression: _Defn):
    return Definition(Operator.AND, (_validate(expression),))


def Not(expression: _Defn):
    return Definition(Operator.NOT, (_validate(expression),))


def Raw(expression: _Defn):
    return Definition(Operator.RAW, (_validate(expression),))


def Discard(expression: _Defn):
    return Definition(Operator.DIS, (_validate(expression),))


def Bind(expression: _Defn, name: str):
    assert isinstance(name, str)
    return Definition(Operator.BND, (name, _validate(expression),))


def Rule(expression: _Defn, action: Callable, name: str = '<anonymous>'):
    return Definition(Operator.RUL, (_validate(expression), action, name))


class Grammar:
    """A parsing expression grammar definition."""

    def __init__(self,
                 definitions: Dict[str, Definition] = None,
                 actions: Dict[str, Callable] = None,
                 start: str = 'Start'):
        self.start = start
        self.definitions = definitions or {}
        self.actions = actions or {}
        self.final = False

    def __repr__(self):
        return (f'Grammar({self.definitions!r}, '
                f'actions={self.actions!r}, '
                f'start={self.start!r})')

    def __setitem__(self, name: str, definition: Definition):
        self.definitions[name] = definition

    def __getitem__(self, name):
        return self.definitions[name]

    def __eq__(self, other: 'Grammar'):
        return (self.start == other.start
                and self.definitions == other.definitions
                and self.actions == other.actions)

    def finalize(self):
        if self.final:
            raise Error('grammar is already finalized')

        self.final = True
