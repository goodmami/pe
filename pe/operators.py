

from typing import Union, Tuple, Dict, Pattern, Callable, Any

from pe._constants import ANONYMOUS, Operator
from pe._errors import Error, GrammarError
from pe._definition import Definition
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
    return Definition(DOT, ())


def Literal(string: str):
    return Definition(LIT, (string,))


def Class(chars: str):
    return Definition(CLS, (chars,))


def Regex(pattern: Union[str, Pattern], flags: int = 0):
    return Definition(RGX, (pattern, flags))


def Sequence(*expressions: _Def):
    exprs = list(map(_validate, expressions))
    if len(exprs) == 1:
        return exprs[0]
    else:
        _exprs = []
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
        _exprs = []
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


def Raw(expression: _Def):
    return Definition(RAW, (_validate(expression),))


def Discard(expression: _Def):
    return Definition(DIS, (_validate(expression),))


def Bind(expression: _Def, name: str):
    assert isinstance(name, str)
    return Definition(BND, (_validate(expression), name))


def Rule(expression: _Def, action: Callable, name: str = ANONYMOUS):
    return Definition(RUL, (_validate(expression), action, name))
