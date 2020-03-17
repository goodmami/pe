
"""
Grammar Definition Merging
"""

import pe
from pe._constants import Operator
from pe.grammar import (
    Literal,
    Class,
    Sequence,
    Regex,
    Choice,
    Repeat,
    Optional,
    Star,
    Plus,
    Nonterminal,
    And,
    Not,
    Bind,
    Rule,
    Grammar,
)


DOT = Operator.DOT
LIT = Operator.LIT
CLS = Operator.CLS
RGX = Operator.RGX
SYM = Operator.SYM
OPT = Operator.OPT
RPT = Operator.RPT
AND = Operator.AND
NOT = Operator.NOT
DIS = Operator.DIS
BND = Operator.BND
SEQ = Operator.SEQ
CHC = Operator.CHC
RUL = Operator.RUL


def optimize(g: Grammar):
    """Join adjacent expressions when possible."""
    defs = {}
    for name in g.definitions:
        defs[name] = _merge(g, g[name])
    return Grammar(definitions=defs,
                   actions=g.actions,
                   start=g.start)


def _merge(g, defn):
    op = defn.op
    args = defn.args

    if op == SEQ:
        return _merge_seq(g, defn)
    elif op == CHC:
        return _merge_chc(g, defn)

    elif op == RPT:
        d, min, max = args
        return Repeat(_merge(g, d), min, max)
    elif op == OPT:
        return Optional(_merge(g, args[0]))
    elif op == AND:
        return And(_merge(g, args[0]))
    elif op == NOT:
        return Not(_merge(g, args[0]))
    elif op == BND:
        name, d = args
        return Bind(_merge(g, d), name=name)
    elif op == RUL:
        return Rule(_merge(g, args[0]), action=args[1])
    else:
        return defn

def _merge_seq(g, defn):
    exprs = defn.args[0]
    _exprs = [_merge(g, exprs[0])]
    prev = _exprs[-1]
    for expr in exprs[1:]:
        if expr.op == prev.op == LIT:
            _exprs[-1] = prev = Literal(prev.args[0] + expr.args[0])
        else:
            _exprs.append(expr)
            prev = expr
    return Sequence(*_exprs)


def _single_char(defn):
    return (defn.op == CLS
            or defn.op == LIT and len(defn.args[0]) == 1)


def _merge_chc(g, defn):
    exprs = defn.args[0]
    _exprs = [_merge(g, exprs[0])]
    prev = _exprs[-1]
    for expr in exprs[1:]:
        if (_single_char(expr) and _single_char(prev)):
            _exprs[-1] = prev = Class(prev.args[0] + expr.args[0])
        else:
            _exprs.append(expr)
            prev = expr
    return Choice(*_exprs)

