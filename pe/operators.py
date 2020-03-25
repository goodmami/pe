

from typing import Union, Tuple, Dict, Pattern, Callable, Any

from pe._constants import ANONYMOUS, Operator
from pe._core import Error


class Definition:
    """An abstract definition of a parsing expression."""
    __slots__ = 'op', 'args',

    def __init__(self, op: Operator, args: Tuple[Any, ...]):
        self.op = op
        self.args = args

    def __repr__(self):
        return f'({self.op}, {self.args!r})'

    def __eq__(self, other: object):
        if not isinstance(other, Definition):
            return NotImplemented
        return (self.op == other.op) and (self.args == other.args)


_Def = Union[str, Definition]


def _validate(arg: _Def):
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


def Sequence(*expressions: _Def):
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


def Choice(*expressions: _Def):
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


def Optional(expression: _Def):
    return Definition(Operator.OPT, (_validate(expression),))


def Star(expression: _Def):
    return Definition(Operator.STR, (_validate(expression),))


def Plus(expression: _Def):
    return Definition(Operator.PLS, (_validate(expression),))


def Nonterminal(name: str):
    return Definition(Operator.SYM, (name,))


def And(expression: _Def):
    return Definition(Operator.AND, (_validate(expression),))


def Not(expression: _Def):
    return Definition(Operator.NOT, (_validate(expression),))


def Raw(expression: _Def):
    return Definition(Operator.RAW, (_validate(expression),))


def Discard(expression: _Def):
    return Definition(Operator.DIS, (_validate(expression),))


def Bind(expression: _Def, name: str):
    assert isinstance(name, str)
    return Definition(Operator.BND, (_validate(expression), name))


def Rule(expression: _Def, action: Callable, name: str = ANONYMOUS):
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

    def __eq__(self, other: object):
        if not isinstance(other, Grammar):
            return NotImplemented
        return (self.start == other.start
                and self.definitions == other.definitions
                and self.actions == other.actions)

    def finalize(self):
        if self.final:
            raise Error('grammar is already finalized')
        defs = self.definitions
        acts = self.actions
        for name in defs:
            expr = defs[name]
            if name in acts:
                if expr.op == Operator.RUL:
                    # check if name is same or None?
                    expr = expr.args[0]
                expr = Rule(expr, acts[name], name=name)
                defs[name] = expr
            _check_closed(expr, defs)
        self.final = True


def _check_closed(expr, defs):
    op = expr.op
    args = expr.args
    if op == Operator.SYM:
        if args[0] not in defs:
            raise Error(f'undefined nonterminal: {args[0]}')
    elif op in (Operator.DOT, Operator.LIT, Operator.CLS, Operator.RGX):
        pass
    elif op in (Operator.SEQ, Operator.CHC):
        for term in args[0]:
            _check_closed(term, defs)
    else:
        _check_closed(args[0], defs)

