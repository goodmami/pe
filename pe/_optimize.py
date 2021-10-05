
"""
Grammar Definition to Regular Expression Conversion
"""

import re
from itertools import groupby, count

from pe._constants import Operator
from pe._errors import Error
from pe._definition import Definition
from pe._grammar import Grammar
from pe.operators import (
    Literal,
    Class,
    Regex,
    Choice,
    Optional,
    Star,
    Plus,
    And,
    Not,
    Capture,
    Bind,
    Sequence,
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


def optimize(g: Grammar, inline=True, common=True, regex=True):
    """Combine adjacent terms into a single regular expression."""
    defs = g.definitions

    if inline:
        new = {}
        for name, defn in defs.items():
            new[name] = _inline(defs, defn, {name})
        defs = new

    if common:
        new = {}
        for name, defn in defs.items():
            new[name] = _common(defn)
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


def _common(defn):
    op = defn.op

    # descend first
    make_op = _op_map.get(op)
    if op in (SEQ, CHC):
        defn = make_op(*(_common(d) for d in defn.args[0]))
    elif make_op:
        defn = make_op(_common(defn.args[0]), *defn.args[1:])

    # [.]  ->  "."  (only 1-char class, not a range, not negated)
    if op == CLS:
        ranges = defn.args[0]
        negated = defn.args[1]
        if len(ranges) == 1 and ranges[0][1] is None and not negated:
            defn = Literal(ranges[0][0])

    if op == SEQ:
        _common_sequence(defn.args[0])

    if op == CHC:
        _common_choice(defn.args[0])

    # Sequence(x)  ->  x  OR  Choice(x)  ->  x
    if op in (SEQ, CHC) and len(defn.args[0]) == 1:
        defn = defn.args[0][0]
        op = defn.op

    return defn


def _common_sequence(subdefs):
    i = 0
    while i < len(subdefs) - 1:
        d = subdefs[i]
        # ![...] .  ->  [^...]
        # !"." .    ->  [^.]
        if (d.op == NOT and subdefs[i+1].op == DOT):
            notd = d.args[0]
            if notd.op == CLS:
                negated = not notd.args[1]
                subdefs[i:i+2] = [Class(notd.args[0], negate=negated)]
            elif notd.op == LIT and len(notd.args[0]) == 1:
                subdefs[i:i+2] = [Class(notd.args[0], negate=True)]
        # "." "."  -> ".."
        elif d.op == LIT:
            j = i + 1
            while j < len(subdefs) and subdefs[j].op == LIT:
                j += 1
            if j - i > 1:
                subdefs[i:j] = [Literal(''.join(x.args[0] for x in subdefs[i:j]))]
        i += 1


def _common_choice(subdefs):
    i = 0
    while i < len(subdefs) - 1:
        d = subdefs[i]
        # [..] / [..]  ->  [....]
        # [..] / "."   ->  [...]
        if (d.op == CLS and not d.args[1]) or (d.op == LIT and len(d.args[0]) == 1):
            ranges = d.args[0] if d.op == CLS else [(d.args[0], None)]
            j = i + 1
            while j < len(subdefs):
                d2 = subdefs[j]
                if d2.op == CLS and not d2.args[1]:
                    ranges.extend(d2.args[0])
                elif d2.op == LIT and len(d2.args[0]) == 1:
                    ranges.append((d2.args[0], None))
                else:
                    break
                j += 1
            if j - i > 1:
                subdefs[i:j] = [Class(ranges)]
        i += 1


def _regex_dot(defn, defs, grpid):
    return Regex('(?s:.)')


def _regex_literal(defn, defs, grpid):
    return Regex(re.escape(defn.args[0]))


def _regex_class(defn, defs, grpid):
    neg = '^' if defn.args[1] else ''
    clsstr = ''.join(
        f'{re.escape(a)}-{re.escape(b)}' if b else re.escape(a)
        for a, b in defn.args[0]
    )
    return Regex(f'[{neg}{clsstr}]')


def _regex_sequence(defn, defs, grpid):
    _subdefs = [_regex(subdef, defs, grpid) for subdef in defn.args[0]]
    subdefs = []
    for k, grp in groupby(_subdefs, key=lambda d: d.op):
        # only join regexes in sequence if unstructured
        if k == RGX:
            subdefs.append(Regex(''.join(d.args[0] for d in grp)))
        else:
            subdefs.extend(grp)

    return Sequence(*subdefs)


def _regex_choice(defn, defs, grpid):
    items = [_regex(d, defs, grpid) for d in defn.args[0]]
    subdefs = []
    for k, grp in groupby(items, key=lambda d: d.op):
        grp = list(grp)
        if k == RGX and len(grp) > 1:
            gid = f'_{next(grpid)}'
            subdefs.append(
                Regex(f'(?=(?P<{gid}>'
                      + '|'.join(sd.args[0] for sd in grp)
                      + f'))(?P={gid})'))
        else:
            subdefs.extend(grp)
    return Choice(*subdefs)


def _regex_optional(defn, defs, grpid):
    subdef = defn.args[0]
    d = _regex(defn.args[0], defs, grpid)
    if d.op == RGX:
        subpat = d.args[0] if subdef.op in (DOT, LIT, CLS) else f'(?:{d.args[0]})'
        return Regex(f'{subpat}?')
    else:
        return Optional(d)


def _regex_star(defn, defs, grpid):
    subdef = defn.args[0]
    d = _regex(subdef, defs, grpid)
    if d.op == RGX:
        subpat = d.args[0] if subdef.op in (DOT, LIT, CLS) else f'(?:{d.args[0]})'
        gid = f'_{next(grpid)}'
        return Regex(f'(?=(?P<{gid}>{subpat}*))(?P={gid})')
    else:
        return Star(d)


def _regex_plus(defn, defs, grpid):
    subdef = defn.args[0]
    d = _regex(defn.args[0], defs, grpid)
    if d.op == RGX:
        subpat = d.args[0] if subdef.op in (DOT, LIT, CLS) else f'(?:{d.args[0]})'
        gid = f'_{next(grpid)}'
        return Regex(f'(?=(?P<{gid}>{subpat}+))(?P={gid})')
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


def regex(defn: Definition):
    # this can be expanded if there are no nonterminals, captures, or actions
    if defn.op not in (DOT, LIT, CLS, RGX):
        raise Error(f'cannot convert {defn.op} to a regular expression')
    elif defn.op != RGX:
        defn = _regex(defn, {}, count(start=1))
    return defn
