
"""
Grammar optimization.
"""

import re
from itertools import groupby

from pe.constants import Operator
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


def inline(g: Grammar):
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

    if op == Operator.SYM:
        name = args[0]
        if name in visited:
            return defn
        else:
            defn = _inline(g, g[name], visited | {name})
            if name in g.actions:
                defn = Rule(defn, action=g.actions[name])
            return defn

    if op == Operator.SEQ:
        return Sequence(*(_inline(g, d, visited) for d in args[0]))
    elif op == Operator.CHC:
        return Choice(*(_inline(g, d, visited) for d in args[0]))
    elif op == Operator.RPT:
        d, min, max = args
        return Repeat(_inline(g, d, visited), min, max)
    elif op == Operator.OPT:
        return Optional(_inline(g, args[0], visited))
    elif op == Operator.AND:
        return And(_inline(g, args[0], visited))
    elif op == Operator.NOT:
        return Not(_inline(g, args[0], visited))
    elif op == Operator.BND:
        name, d = args
        return Bind(_inline(g, d, visited), name=name)
    elif op == Operator.RUL:
        return Rule(_inline(g, args[0], visited), action=args[1])
    else:
        return defn


def merge(g: Grammar):
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

    if op == Operator.SEQ:
        return _merge_seq(g, defn)
    elif op == Operator.CHC:
        return _merge_chc(g, defn)

    elif op == Operator.RPT:
        d, min, max = args
        return Repeat(_merge(g, d), min, max)
    elif op == Operator.OPT:
        return Optional(_merge(g, args[0]))
    elif op == Operator.AND:
        return And(_merge(g, args[0]))
    elif op == Operator.NOT:
        return Not(_merge(g, args[0]))
    elif op == Operator.BND:
        name, d = args
        return Bind(_merge(g, d), name=name)
    elif op == Operator.RUL:
        return Rule(_merge(g, args[0]), action=args[1])
    else:
        return defn

def _merge_seq(g, defn):
    exprs = defn.args[0]
    _exprs = [_merge(g, exprs[0])]
    prev = _exprs[-1]
    for expr in exprs[1:]:
        if expr.op == prev.op == Operator.LIT:
            _exprs[-1] = prev = Literal(prev.args[0] + expr.args[0])
        else:
            _exprs.append(expr)
            prev = expr
    return Sequence(*_exprs)


def _single_char(defn):
    return (defn.op == Operator.CLS
            or defn.op == Operator.LIT and len(defn.args[0]) == 1)


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


def regex(g: Grammar):
    """Combine adjacent terms into a single regular expression."""
    defs = {}
    for name in g.definitions:
        defs[name] = _regex(g, g[name], True)
    return Grammar(definitions=defs,
                   actions=g.actions,
                   start=g.start)


def _regex(g, defn, structured):
    op = defn.op
    args = defn.args

    if op == Operator.DOT:
        return Regex('.')
    elif op == Operator.LIT:
        return Regex(re.escape(args[0]))
    elif op == Operator.CLS:
        return Regex(f'[{args[0]}]')

    elif op == Operator.SEQ:
        exprs = args[0]
        _exprs = []
        i = 0
        # Special case: ![abc] . -> [^abc]
        while i < len(exprs):
            d = exprs[i]
            if (i != len(exprs) - 1
                    and d.op == Operator.NOT
                    and _single_char(d.args[0])
                    and exprs[i+1].op == Operator.DOT):
                _exprs.append(Regex(f'[^{d.args[0].args[0]}]'))
                i += 2
            else:
                _exprs.append(_regex(g, d, structured))
                i += 1
        # combine adjacent regexes
        _exprs2 = []
        for k, g in groupby(_exprs, key=lambda d: d.op):
            if k == Operator.RGX:
                _exprs2.append(Regex(''.join(d.args[0] for d in g)))
            else:
                _exprs2.extend(g)
        return Sequence(*_exprs2)

    elif op == Operator.CHC:
        exprs = [_regex(g, d, structured) for d in args[0]]
        _exprs = []
        for k, g in groupby(exprs, key=lambda d: d.op):
            if k == Operator.RGX:
                _exprs.append(
                    Regex('(?:' + '|'.join(d.args[0] for d in g) + ')'))
            else:
                _exprs.extend(g)
        return Choice(*_exprs)

    elif op == Operator.RPT:
        d, min, max = args
        d = _regex(g, d, structured)
        if d.op == Operator.RGX:
            q = _quantifier_re(min, max)
            return Regex('(?:' + d.args[0] + f'){q}')
        else:
            return Repeat(d, min, max)

    elif op == Operator.OPT:
        d = _regex(g, args[0], structured)
        if d.op == Operator.RGX:
            return Regex(f'(?:{d.args[0]})?')
        else:
            return Optional(d)

    elif op == Operator.AND:
        d = _regex(g, args[0], structured)
        if d.op == Operator.RGX:
            return Regex(f'(?={d.args[0]})')
        else:
            return And(d)

    elif op == Operator.NOT:
        d = _regex(g, args[0], structured)
        if d.op == Operator.RGX:
            return Regex(f'(?!{d.args[0]})')
        else:
            return Not(d)

    elif op == Operator.BND:
        name, d = args
        return Bind(_regex(g, d, structured), name=name)
    elif op == Operator.RUL:
        return Rule(_regex(g, args[0], structured), action=args[1])
    else:
        return defn


_special_quantifiers = {
    #min max
    (1, 1): '',
    (0, 1): '?',
    (0, -1): '*',
    (1, -1): '+',
}


def _quantifier_re(min, max):
    q = _special_quantifiers.get((min, max))
    if not q:
        if min == max:
            q = f'{{{max}}}'
        else:
            min = '' if min == 0 else min
            max = '' if max < 0 else max
            q = f'{{{min},{max}}}'
    return q

