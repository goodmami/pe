

from typing import Union, List, Tuple, Dict, Pattern, Callable, overload

from pe._constants import ANONYMOUS, Operator
from pe._errors import GrammarError
from pe._definition import Definition
from pe.actions import Action, Call


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
CAP = Operator.CAP
BND = Operator.BND
SEQ = Operator.SEQ
CHC = Operator.CHC
RUL = Operator.RUL
DBG = Operator.DBG


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


def Dot():
    return Definition(DOT, ())


def Literal(string: str):
    return Definition(LIT, (string,))


@overload
def Class(arg: str, negate: bool = ...) -> Definition:
    ...


@overload
def Class(arg: List[Tuple[str, Union[str, None]]], negate: bool = ...) -> Definition:
    ...


def Class(arg, negate: bool = False):
    ranges: List[Tuple[str, Union[str, None]]]
    if isinstance(arg, list):
        ranges = arg
    else:
        assert isinstance(arg, str)
        ranges = []
        i = 0
        while i < len(arg) - 2:
            if arg[i+1] == '-':
                ranges.append((arg[i], arg[i+2]))
                i += 3
            else:
                ranges.append((arg[i], None))
                i += 1
        while i < len(arg):
            ranges.append((arg[i], None))
            i += 1

    return Definition(CLS, (ranges, negate))


def Regex(pattern: Union[str, Pattern], flags: int = 0):
    return Definition(RGX, (pattern, flags))


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
        return Definition(SEQ, (_exprs,))


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
        return Definition(CHC, (_exprs,))


def Optional(expression: _Def):
    expression = _validate(expression)
    if expression.op in (OPT, STR, PLS):
        raise GrammarError('multiple repeat operators')
    return Definition(OPT, (expression,))


def Star(expression: _Def):
    expression = _validate(expression)
    if expression.op in (OPT, STR, PLS):
        raise GrammarError('multiple repeat operators')
    return Definition(STR, (expression,))


def Plus(expression: _Def):
    expression = _validate(expression)
    if expression.op in (OPT, STR, PLS):
        raise GrammarError('multiple repeat operators')
    return Definition(PLS, (expression,))


def Nonterminal(name: str):
    return Definition(SYM, (name,))


def And(expression: _Def):
    return Definition(AND, (_validate(expression),))


def Not(expression: _Def):
    return Definition(NOT, (_validate(expression),))


def Capture(expression: _Def):
    return Definition(CAP, (_validate(expression),))


def Bind(expression: _Def, name: str):
    assert isinstance(name, str)
    return Definition(BND, (_validate(expression), name))


def Rule(expression: _Def, action: Callable, name: str = ANONYMOUS):
    if action and not isinstance(action, Action):
        action = Call(action)
    return Definition(RUL, (_validate(expression), action, name))


def Debug(expression: _Def):
    return Definition(DBG, (_validate(expression),))


class SymbolTable(Dict[str, Definition]):
    """Dictionary subclass for simplifying grammar construction."""

    def __setattr__(self, name: str, value: Definition) -> None:
        dict.__setitem__(self, name, value)

    def __getattr__(self, name: str) -> Definition:
        return Nonterminal(name)
