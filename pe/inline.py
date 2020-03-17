
"""
Grammar Definition Inlining
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
    """Inline non-recursive grammar rules."""
    defs = {}
    for name in g.definitions:
        defs[name] = _inline(g, g[name], {name})
    return Grammar(definitions=defs,
                   actions=g.actions,
                   start=g.start)

def _inline(g, defn, visited):
    op = defn.op
    args = defn.args

    if op == SYM:
        name = args[0]
        if name in visited:
            return defn
        else:
            defn = _inline(g, g[name], visited | {name})
            if name in g.actions:
                defn = Rule(defn, action=g.actions[name])
            return defn

    if op == SEQ:
        return Sequence(*(_inline(g, d, visited) for d in args[0]))
    elif op == CHC:
        return Choice(*(_inline(g, d, visited) for d in args[0]))
    elif op == RPT:
        d, min, max = args
        return Repeat(_inline(g, d, visited), min, max)
    elif op == OPT:
        return Optional(_inline(g, args[0], visited))
    elif op == AND:
        return And(_inline(g, args[0], visited))
    elif op == NOT:
        return Not(_inline(g, args[0], visited))
    elif op == BND:
        name, d = args
        return Bind(_inline(g, d, visited), name=name)
    elif op == RUL:
        return Rule(_inline(g, args[0], visited), action=args[1])
    else:
        return defn
