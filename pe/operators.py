

from typing import Union, Tuple, Dict, Pattern, Callable, Any

from pe._constants import ANONYMOUS, Operator
from pe._core import Error, GrammarError, Definition


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
    expression = _validate(expression)
    if expression.op in (Operator.OPT, Operator.STR, Operator.PLS):
        raise GrammarError('multiple repeat operators')
    return Definition(Operator.OPT, (expression,))


def Star(expression: _Def):
    expression = _validate(expression)
    if expression.op in (Operator.OPT, Operator.STR, Operator.PLS):
        raise GrammarError('multiple repeat operators')
    return Definition(Operator.STR, (expression,))


def Plus(expression: _Def):
    expression = _validate(expression)
    if expression.op in (Operator.OPT, Operator.STR, Operator.PLS):
        raise GrammarError('multiple repeat operators')
    return Definition(Operator.PLS, (expression,))


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
