
"""
Grammar Definition to Regular Expression Conversion
"""

import re
from itertools import groupby, count

import pe
from pe._constants import Operator
from pe.grammar import (
    Literal,
    Class,
    Sequence,
    Regex,
    Choice,
    Optional,
    Star,
    Plus,
    Nonterminal,
    And,
    Not,
    Bind,
    Discard,
    Rule,
    Grammar,
)


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
DIS = Operator.DIS
BND = Operator.BND
SEQ = Operator.SEQ
CHC = Operator.CHC
RUL = Operator.RUL


def optimize(g: Grammar):
    """Combine adjacent terms into a single regular expression."""
    defs = {}
    grpid = count(start=1)
    for name in g.definitions:
        defs[name] = _regex(g, g[name], True, grpid)
    return Grammar(definitions=defs,
                   actions=g.actions,
                   start=g.start)


def _regex(g, defn, structured, grpid):
    op = defn.op
    args = defn.args

    if op == DOT:
        return Regex('.')
    elif op == LIT:
        return Regex(re.escape(args[0]))
    elif op == CLS:
        return Regex(f'[{args[0]}]')

    elif op == SEQ:
        exprs = _seq_first_pass(g, args[0], structured, grpid)
        exprs = _seq_join_unstructured(exprs, structured)
        return Sequence(*exprs)

    elif op == CHC:
        exprs = [_regex(g, d, structured, grpid) for d in args[0]]
        _exprs = []
        for k, grp in groupby(exprs, key=lambda d: d.op):
            if k == RGX:
                gid = f'_{next(grpid)}'
                _exprs.append(
                    Regex(f'(?=(?P<{gid}>'
                          + '|'.join(d.args[0] for d in grp)
                          + f'))(?P={gid})'))
            else:
                _exprs.extend(grp)
        return Choice(*_exprs)

    elif op == OPT:
        d = _regex(g, args[0], structured, grpid)
        if d.op == RGX:
            return Regex(f'(?:{d.args[0]})?')
        else:
            return Optional(d)

    elif op == STR:
        d = _regex(g, args[0], structured, grpid)
        if d.op == RGX:
            gid = f'_{next(grpid)}'
            return Regex(f'(?=(?P<{gid}>(?:' + d.args[0] + f')*))(?P={gid})')
        else:
            return Star(d)

    elif op == PLS:
        d = _regex(g, args[0], structured, grpid)
        if d.op == RGX:
            gid = f'_{next(grpid)}'
            return Regex(f'(?=(?P<{gid}>(?:' + d.args[0] + f')+))(?P={gid})')
        else:
            return Plus(d)

    elif op == AND:
        d = _regex(g, args[0], structured, grpid)
        if d.op == RGX:
            return Regex(f'(?={d.args[0]})')
        else:
            return And(d)

    elif op == NOT:
        d = _regex(g, args[0], structured, grpid)
        if d.op == RGX:
            return Regex(f'(?!{d.args[0]})')
        else:
            return Not(d)

    elif op == BND:
        name, d = args
        return Bind(_regex(g, d, structured, grpid), name=name)

    elif op == DIS:
        d = _regex(g, args[0], False, grpid)
        return Discard(d)

    elif op == RUL:
        return Rule(_regex(g, args[0], structured, grpid), action=args[1])
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


def _single_char(defn):
    return (defn.op == CLS
            or defn.op == LIT and len(defn.args[0]) == 1)


def _seq_first_pass(g, exprs, structured, grpid):
    i = 0
    # Special case: ![abc] . -> [^abc]
    while i < len(exprs):
        d = exprs[i]
        if (i != len(exprs) - 1
                and d.op == NOT
                and _single_char(d.args[0])
                and exprs[i+1].op == DOT):
            yield Regex(f'[^{d.args[0].args[0]}]')
            i += 2
        else:
            yield _regex(g, d, structured, grpid)
            i += 1


def _seq_join_unstructured(exprs, structured):
    for k, grp in groupby(exprs, key=lambda d: d.op):
        # only join regexes in sequence if unstructured
        if k == RGX and not structured:
            yield Regex(''.join(d.args[0] for d in grp))
        # sequences of discarded things can get joined (e.g., ':"a" :"b"')
        elif k == DIS:
            discarded = [d.args[0] for d in grp]
            for d in _seq_join_unstructured(discarded, False):
                yield Discard(d)
        else:
            yield from grp
