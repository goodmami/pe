
"""
Grammar Definition to Regular Expression Conversion
"""

import re
from itertools import groupby, count

import pe
from pe._constants import Operator
from pe._grammar import Grammar
from pe.operators import (
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
    Raw,
    Bind,
    Discard,
    Rule,
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
RAW = Operator.RAW
DIS = Operator.DIS
BND = Operator.BND
SEQ = Operator.SEQ
CHC = Operator.CHC
RUL = Operator.RUL


def optimize(g: Grammar, inline=True, regex=True):
    """Combine adjacent terms into a single regular expression."""
    defs = g.definitions

    if inline:
        new = {}
        for name, defn in defs.items():
            new[name] = _inline(defs, defn, {name})
        defs = new

    if regex:
        new = {}
        grpid = count(start=1)
        for name, defn in defs.items():
            new[name] = _regex(defs, defn, True, grpid)
        defs = new

    return Grammar(definitions=defs,
                   actions=g.actions,
                   start=g.start)


def _inline(defs, defn, visited):
    op = defn.op
    args = defn.args

    if op == SYM:
        name = args[0]
        if name in visited:  # recursive rule
            return defn
        else:
            return _inline(defs, defs[name], visited | {name})

    elif op == SEQ:
        return Sequence(*(_inline(defs, d, visited) for d in args[0]))
    elif op == CHC:
        return Choice(*(_inline(defs, d, visited) for d in args[0]))
    elif op == OPT:
        return Optional(_inline(defs, args[0], visited))
    elif op == STR:
        return Star(_inline(defs, args[0], visited))
    elif op == PLS:
        return Plus(_inline(defs, args[0], visited))
    elif op == AND:
        return And(_inline(defs, args[0], visited))
    elif op == NOT:
        return Not(_inline(defs, args[0], visited))
    elif op == RAW:
        return Raw(_inline(defs, args[0], visited))
    elif op == DIS:
        return Discard(_inline(defs, args[0], visited))
    elif op == BND:
        d, name = args
        return Bind(_inline(defs, d, visited), name=name)
    elif op == RUL:
        return Rule(_inline(defs, args[0], visited), args[1], name=args[2])
    else:
        return defn


def _regex(defs, defn, structured, grpid):
    op = defn.op
    args = defn.args

    if op == DOT:
        return Regex('.')
    elif op == LIT:
        return Regex(re.escape(args[0]))
    elif op == CLS:
        return Regex(f'[{args[0]}]')

    elif op == SEQ:
        exprs = _seq_first_pass(defs, args[0], structured, grpid)
        exprs = _seq_join_unstructured(exprs, structured)
        return Sequence(*exprs)

    elif op == CHC:
        exprs = [_regex(defs, d, structured, grpid) for d in args[0]]
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
        d = _regex(defs, args[0], structured, grpid)
        if d.op == RGX:
            return Regex(f'(?:{d.args[0]})?')
        else:
            return Optional(d)

    elif op == STR:
        d = _regex(defs, args[0], structured, grpid)
        if d.op == RGX:
            gid = f'_{next(grpid)}'
            return Regex(f'(?=(?P<{gid}>(?:' + d.args[0] + f')*))(?P={gid})')
        else:
            return Star(d)

    elif op == PLS:
        d = _regex(defs, args[0], structured, grpid)
        if d.op == RGX:
            gid = f'_{next(grpid)}'
            return Regex(f'(?=(?P<{gid}>(?:' + d.args[0] + f')+))(?P={gid})')
        else:
            return Plus(d)

    elif op == AND:
        d = _regex(defs, args[0], structured, grpid)
        if d.op == RGX:
            return Regex(f'(?={d.args[0]})')
        else:
            return And(d)

    elif op == NOT:
        d = _regex(defs, args[0], structured, grpid)
        if d.op == RGX:
            return Regex(f'(?!{d.args[0]})')
        else:
            return Not(d)

    elif op == RAW:
        return Raw(_regex(defs, args[0], False, grpid))

    elif op == BND:
        d, name = args
        return Bind(_regex(defs, d, structured, grpid), name=name)

    elif op == DIS:
        d = _regex(defs, args[0], False, grpid)
        return Discard(d)

    elif op == RUL:
        return Rule(_regex(defs, args[0], structured, grpid),
                    args[1],
                    name=args[2])
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


def _seq_first_pass(defs, exprs, structured, grpid):
    i = 0
    # Special case: ![abc] . -> [^abc]
    while i < len(exprs):
        d = exprs[i]
        if (i != len(exprs) - 1 and d.op == NOT and exprs[i+1].op == DOT):
            notd = d.args[0]
            if notd.op == CLS:
                yield Regex(f'[^{notd.args[0]}]')
                i += 1
            elif notd.op == LIT and len(notd.args[0]) == 1:
                yield Regex(f'[^{re.escape(notd.args[0])}]')
                i += 1
            else:
                yield _regex(defs, d, structured, grpid)
        else:
            yield _regex(defs, d, structured, grpid)
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
