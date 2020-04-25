
"""
Grammar Definition to Regular Expression Conversion
"""

import re
from itertools import groupby, count

from pe._constants import Operator
from pe._definition import Definition
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
    Capture,
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
CAP = Operator.CAP
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
            new[name] = _regex(defn, defs, grpid)
        defs = new

    return Grammar(definitions=defs,
                   actions=g.actions,
                   start=g.start)


# only need to map mutually recursive operators
_op_map = {
    OPT: Optional,
    STR: Star,
    PLS: Plus,
    AND: And,
    NOT: Not,
    CAP: Capture,
    BND: Bind,
    SEQ: Sequence,
    CHC: Choice,
    RUL: Rule,
}


def _inline(defs, defn, visited):
    op = defn.op
    args = defn.args

    # only nonterminals (SYM) can be inlined
    if op == SYM:
        name = args[0]
        if (name in visited                # recursive definition
            or (defs[name].op == RUL       # rule with action
                and defs[name].args[1])):
            return defn
        else:
            return _inline(defs, defs[name], visited | {name})
    # for all others, just pass through
    else:
        make_op = _op_map.get(op)
        if op in (SEQ, CHC):
            return make_op(*(_inline(defs, d, visited) for d in args[0]))
        elif make_op:
            return make_op(_inline(defs, args[0], visited), *args[1:])
        else:
            return defn


def _regex_dot(defn, defs, grpid):
    return Regex('.')


def _regex_literal(defn, defs, grpid):
    return Regex(re.escape(defn.args[0]))


def _regex_class(defn, defs, grpid):
    return Regex(f'[{defn.args[0]}]')


def _regex_sequence(defn, defs, grpid):
    subdefs = _seq_first_pass(defs, defn.args[0], grpid)
    subdefs = _seq_join_unstructured(subdefs)
    return Sequence(*subdefs)


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
                yield _regex(d, defs, grpid)
        else:
            yield _regex(d, defs, grpid)
        i += 1


def _seq_join_unstructured(subdefs):
    for k, grp in groupby(subdefs, key=lambda d: d.op):
        # only join regexes in sequence if unstructured
        if k == RGX:
            yield Regex(''.join(d.args[0] for d in grp))
        else:
            yield from grp


def _regex_choice(defn, defs, grpid):
    items = [_regex(d, defs, grpid) for d in defn.args[0]]
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


def _regex_optional(defn, defs, grpid):
    d = _regex(defn.args[0], defs, grpid)
    if d.op == RGX:
        return Regex(f'(?:{d.args[0]})?')
    else:
        return Optional(d)


def _regex_star(defn, defs, grpid):
    d = _regex(defn.args[0], defs, grpid)
    if d.op == RGX:
        gid = f'_{next(grpid)}'
        return Regex(f'(?=(?P<{gid}>(?:'
                     + d.args[0]
                     + f')*))(?P={gid})')
    else:
        return Star(d)


def _regex_plus(defn, defs, grpid):
    d = _regex(defn.args[0], defs, grpid)
    if d.op == RGX:
        gid = f'_{next(grpid)}'
        return Regex(f'(?=(?P<{gid}>(?:'
                     + d.args[0]
                     + f')+))(?P={gid})')
    else:
        return Plus(d)


def _regex_and(defn, defs, grpid):
    d = _regex(defn.args[0], defs, grpid)
    if d.op == RGX:
        return Regex(f'(?={d.args[0]})')
    else:
        return And(d)


def _regex_not(defn, defs, grpid):
    d = _regex(defn.args[0], defs, grpid)
    if d.op == RGX:
        return Regex(f'(?!{d.args[0]})')
    else:
        return Not(d)


def _regex_capture(defn, defs, grpid):
    subdef = _regex(defn.args[0], defs, grpid)
    return Capture(subdef)


def _regex_bind(defn, defs, grpid):
    d, name = defn.args
    subdef = _regex(d, defs, grpid)
    return Bind(subdef, name=name)


def _regex_rule(defn, defs, grpid):
    subdef, action, name = defn.args
    newdefn = _regex(subdef, defs, grpid)
    if action is not None:
        newdefn = Rule(newdefn, action, name=name)
    return newdefn


_regex_op_map = {
    DOT: _regex_dot,
    LIT: _regex_literal,
    CLS: _regex_class,
    OPT: _regex_optional,
    STR: _regex_star,
    PLS: _regex_plus,
    AND: _regex_and,
    NOT: _regex_not,
    CAP: _regex_capture,
    BND: _regex_bind,
    SEQ: _regex_sequence,
    CHC: _regex_choice,
    RUL: _regex_rule,
}


def _regex(defn: Definition, defs, grpid):
    """
    Convert patterns to regular expressions if they do not emit or
    bind values.

    Note: this assumes that any Regex operator does not emit or bind
    values.
    """
    # TODO: when merging regexes with flags, use local flags,
    #       (?imsx:-imsx:...)
    func = _regex_op_map.get(defn.op)
    if func:
        rgx = func(defn, defs, grpid)
        return rgx
    else:
        return defn
