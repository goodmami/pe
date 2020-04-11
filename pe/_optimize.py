
"""
Grammar Definition to Regular Expression Conversion
"""

import re
from itertools import groupby, count

from pe._constants import Operator
from pe._grammar import Grammar
from pe.operators import (
    Sequence,
    Regex,
    Choice,
    Optional,
    Star,
    Plus,
    And,
    Not,
    Raw,
    Bind,
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
            new[name] = _regex(defs, defn, grpid)
        defs = new

    return Grammar(definitions=defs,
                   actions=g.actions,
                   start=g.start)


def _inline(defs, defn, visited):
    op = defn.op
    args = defn.args

    if op == SYM:
        name = args[0]
        if name in visited:  # recursive definition
            return defn
        elif defs[name].op == RUL and defs[name].args[1]:  # rule with action
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
    elif op == BND:
        d, name = args
        return Bind(_inline(defs, d, visited), name=name)
    elif op == RUL:
        d, action, name = args
        return Rule(_inline(defs, d, visited), action, name=name)
    else:
        return defn


def _regex(defs, defn, grpid):
    """
    Convert patterns to regular expressions if they do not emit or
    bind values.

    Note: this assumes that any Regex operator does not emit or bind
    values.
    """
    # TODO: when merging regexes with flags, use local flags,
    #       (?imsx:-imsx:...)
    op = defn.op
    args = defn.args

    if op == DOT:
        return Regex('.')
    elif op == LIT:
        return Regex(re.escape(args[0]))
    elif op == CLS:
        return Regex(f'[{args[0]}]')

    elif op == SEQ:
        subdefs = _seq_first_pass(defs, args[0], grpid)
        subdefs = _seq_join_unstructured(subdefs)
        return Sequence(*subdefs)

    elif op == CHC:
        items = [_regex(defs, d, grpid) for d in args[0]]
        subdefs = []
        for k, grp in groupby(items, key=lambda d: d.op):
            if k == RGX:
                gid = f'_{next(grpid)}'
                subdefs.append(
                    Regex(f'(?=(?P<{gid}>'
                          + '|'.join(sd.args[0] for sd in grp)
                          + f'))(?P={gid})'))
            else:
                subdefs.extend(grp)
        return Choice(*subdefs)

    elif op == OPT:
        d = _regex(defs, args[0], grpid)
        if d.op == RGX:
            return Regex(f'(?:{d.args[0]})?')
        else:
            return Optional(d)

    elif op == STR:
        d = _regex(defs, args[0], grpid)
        if d.op == RGX:
            gid = f'_{next(grpid)}'
            return Regex(f'(?=(?P<{gid}>(?:'
                         + d.args[0]
                         + f')*))(?P={gid})')
        else:
            return Star(d)

    elif op == PLS:
        d = _regex(defs, args[0], grpid)
        if d.op == RGX:
            gid = f'_{next(grpid)}'
            return Regex(f'(?=(?P<{gid}>(?:'
                         + d.args[0]
                         + f')+))(?P={gid})')
        else:
            return Plus(d)

    elif op == AND:
        d = _regex(defs, args[0], grpid)
        if d.op == RGX:
            return Regex(f'(?={d.args[0]})')
        else:
            return And(d)

    elif op == NOT:
        d = _regex(defs, args[0], grpid)
        if d.op == RGX:
            return Regex(f'(?!{d.args[0]})')
        else:
            return Not(d)

    elif op == RAW:
        subdef = _regex(defs, args[0], grpid)
        return Raw(subdef)

    elif op == BND:
        d, name = args
        subdef = _regex(defs, d, grpid)
        return Bind(subdef, name=name)

    elif op == RUL:
        subdef, action, name = args
        _subdef = _regex(defs, subdef, grpid)
        if action is None:
            return _subdef
        else:
            return Rule(_subdef, action, name=name)

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


def _seq_first_pass(defs, subdefs, grpid):
    i = 0
    # Special case: ![abc] . -> [^abc]
    while i < len(subdefs):
        d = subdefs[i]
        if (i != len(subdefs) - 1 and d.op == NOT and subdefs[i+1].op == DOT):
            notd = d.args[0]
            if notd.op == CLS:
                yield Regex(f'[^{notd.args[0]}]')
                i += 1
            elif notd.op == LIT and len(notd.args[0]) == 1:
                yield Regex(f'[^{re.escape(notd.args[0])}]')
                i += 1
            else:
                yield _regex(defs, d, grpid)
        else:
            yield _regex(defs, d, grpid)
        i += 1


def _seq_join_unstructured(subdefs):
    for k, grp in groupby(subdefs, key=lambda d: d.op):
        # only join regexes in sequence if unstructured
        if k == RGX:
            yield Regex(''.join(d.args[0] for d in grp))
        else:
            yield from grp
