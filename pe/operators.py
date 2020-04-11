

from typing import Union, List, Dict, Tuple, Pattern, Callable

from pe._constants import ANONYMOUS, Operator, Value
from pe._errors import GrammarError
from pe._definition import Definition


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


_Def = Union[str, Definition]


def _validate(arg: _Def) -> Definition:
    if isinstance(arg, str):
        return Literal(arg)
    elif not isinstance(arg, Definition):
        raise ValueError(f'not a valid definition: {arg!r}')
    elif not isinstance(arg.op, Operator):
        raise ValueError(f'not a valid operator: {arg.op!r}')
    else:
        return arg


def _atomic(op: Operator, args: Tuple) -> Definition:
    return Definition(op, args, Value.ATOMIC)


def _iterable(op: Operator, args: Tuple) -> Definition:
    return Definition(op, args, Value.ITERABLE)


def _empty(op: Operator, args: Tuple) -> Definition:
    return Definition(op, args, Value.EMPTY)


def _deferred(op: Operator, args: Tuple) -> Definition:
    return Definition(op, args, Value.DEFERRED)


def Dot():
    return _empty(DOT, ())


def Literal(string: str):
    return _empty(LIT, (string,))


def Class(chars: str):
    return _empty(CLS, (chars,))


def Regex(pattern: Union[str, Pattern], flags: int = 0):
    return _empty(RGX, (pattern, flags))


def Sequence(*expressions: _Def):
    exprs = list(map(_validate, expressions))
    if len(exprs) == 1:
        return exprs[0]
    else:
        _exprs: List[Definition] = []
        for expr in exprs:
            if expr.op == SEQ:
                _exprs.extend(expr.args[0])
            else:
                _exprs.append(expr)
        return _iterable(SEQ, (_exprs,))


def Choice(*expressions: _Def):
    exprs = list(map(_validate, expressions))
    if len(exprs) == 1:
        return exprs[0]
    else:
        _exprs: List[Definition] = []
        for expr in exprs:
            if expr.op == CHC:
                _exprs.extend(expr.args[0])
            else:
                _exprs.append(expr)
        return _iterable(CHC, (_exprs,))


def Optional(expression: _Def):
    expression = _validate(expression)
    if expression.op in (OPT, STR, PLS):
        raise GrammarError('multiple repeat operators')
    return _iterable(OPT, (expression,))


def Star(expression: _Def):
    expression = _validate(expression)
    if expression.op in (OPT, STR, PLS):
        raise GrammarError('multiple repeat operators')
    return _iterable(STR, (expression,))


def Plus(expression: _Def):
    expression = _validate(expression)
    if expression.op in (OPT, STR, PLS):
        raise GrammarError('multiple repeat operators')
    return _iterable(PLS, (expression,))


def Nonterminal(name: str):
    return _deferred(SYM, (name,))


def And(expression: _Def):
    return _empty(AND, (_validate(expression),))


def Not(expression: _Def):
    return _empty(NOT, (_validate(expression),))


def Raw(expression: _Def):
    return _atomic(RAW, (_validate(expression),))


def Bind(expression: _Def, name: str):
    assert isinstance(name, str)
    return _empty(BND, (_validate(expression), name))


def Rule(expression: _Def, action: Callable, name: str = ANONYMOUS):
    vtype = _deferred if action is None else _atomic
    return vtype(RUL, (_validate(expression), action, name))


class SymbolTable(Dict[str, Definition]):
    """Dictionary subclass for simplifying grammar construction."""

    # Not sure how to fix this for the type checker yet
    __setattr__ = dict.__setitem__  # type: ignore

    def __getattr__(self, name: str) -> Definition:
        return Nonterminal(name)
