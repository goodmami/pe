
import pytest

import pe
from pe._constants import FAIL
from pe.operators import (
    Dot,
    Literal as Lit,
    Class as Cls,
    Regex as Rgx,
    Nonterminal as Non,
    Optional as Opt,
    Star as Str,
    Plus as Pls,
    And,
    Not,
    Bind as Bnd,
    Raw,
    Sequence as Seq,
    Choice as Chc,
    Rule as Rul,
)
from pe._grammar import Grammar as Grm
from pe.packrat import PackratParser


# don't reuse these in value-changing operations like Bind
abc = Cls('abc')
xyz = Cls('xyz')
abseq = Seq('a', 'b')

_noatom = ((), {}, None)
_noiter = ((), {}, ())

data = [  # noqa: E127
    # id     definition       input,   pos,scan, (groups, groupdict, value)
    ('Dot0', Dot(),           'aaa',    0, 1,    _noatom),
    ('Dot1', Dot(),           '   ',    0, 1,    _noatom),
    ('Dot2', Dot(),           '',       0, FAIL, None),

    ('Lit0', Lit('a',),       'a',      0, 1,    _noatom),
    ('Lit1', Lit('a',),       'aa',     0, 1,    _noatom),
    ('Lit2', Lit('a',),       'b',      0, FAIL, None),
    ('Lit3', Lit('a',),       'a',      1, FAIL, None),
    ('Lit4', Lit('a',),       'ab',     1, FAIL, None),
    ('Lit5', Lit('b',),       'ab',     0, FAIL, None),
    ('Lit6', Lit('b',),       'ab',     1, 2,    _noatom),
    ('Lit7', Lit('abc',),     'abcabc', 0, 3,    _noatom),
    ('Lit8', Lit('abc',),     'abcabc', 1, FAIL, None),
    ('Lit9', Lit('abc',),     'abcabc', 3, 6,    _noatom),

    ('Cls0', Cls('[ab]',),    'a',      0, 1,    _noatom),
    ('Cls1', Cls('[ab]',),    'aa',     0, 1,    _noatom),
    ('Cls2', Cls('[ab]',),    'b',      0, 1,    _noatom),
    ('Cls3', Cls('[ab]',),    'a',      1, FAIL, None),
    ('Cls4', Cls('[ab]',),    'ab',     1, 2,    _noatom),

    ('Rgx0', Rgx('a*'),       'aaa',    0, 3,    _noatom),
    ('Rgx1', Rgx('a|b',),     'b',      0, 1,    _noatom),
    ('Rgx2', Rgx('(?:a)(b)(?:c)(d)',),
                              'abcd',   0, 4,    _noatom),

    ('Opt0', Opt(abc),        'd',      0, 0,    _noiter),
    ('Opt1', Opt(abc),        'ab',     0, 1,    _noiter),
    ('Opt2', Opt(abseq),      'd',      0, 0,    _noiter),
    ('Opt3', Opt(abseq),      'ab',     0, 2,    _noiter),

    ('Str0', Str(abc),        '',       0, 0,    _noiter),
    ('Str1', Str(abc),        'aabbc',  0, 5,    _noiter),

    ('Pls0', Pls(abc,),       '',       0, FAIL, None),
    ('Pls1', Pls(abc,),       'aabbc',  0, 5,    _noiter),

    ('And0', And(abc),        'a',      0, 0,    _noatom),
    ('And1', And(abc),        'd',      0, FAIL, None),

    ('Not0', Not(abc),        'a',      0, FAIL, None),
    ('Not1', Not(abc),        'd',      0, 0,    _noatom),

    ('Bnd0', Bnd(Cls('abc'), name='x'),
                              'a',      0, 1,    ((), {'x': None}, None)),

    ('Seq0', Seq(abc),        'aaa',    0, 1,    _noatom),
    ('Seq1', Seq(abc, abc),   'bbb',    0, 2,    _noiter),
    ('Seq2', Seq(abc),        'd',      0, FAIL, None),

    ('Chc0', Chc(abc),        'aaa',    0, 1,    _noatom),
    ('Chc1', Chc(abc, abc),   'aaa',    0, 1,    _noiter),
    ('Chc2', Chc(abc, xyz),   'yyy',    0, 1,    _noiter),
    ('Chc3', Chc(abc, xyz),   'd',      0, FAIL, None),

    ('Raw1', Raw(Dot()),      'abc',    0, 1,    (('a',), {}, 'a')),
    ('Raw2', Raw(abc),        'cba',    0, 1,    (('c',), {}, 'c')),
    ('Raw3', Str(Raw(abc)),   'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                                  {},
                                                  ('a', 'a', 'b', 'b', 'c',))),
    ('Raw4', Raw(Str(abc)),   'aabbc',  0, 5,    (('aabbc',), {}, 'aabbc')),
    ('Raw5', Seq(Raw(abc), Cls('xyz'), Raw(abc)),
                              'axb',    0, 3,    (('a', 'b'), {}, ('a', 'b'))),

    ('Rul0', Rul(abc, None),  'a',      0, 1,    _noatom),
    ('Rul1', Rul(Raw(abc), None), 'a',  0, 1,    (('a',), {}, 'a')),
    ('Rul2', Rul(abc, None),  'd',      0, FAIL, None),
    ('Rul3', Rul(Raw(abc), lambda x: int(x, 16), name='A'),
                              'a',      0, 1,    ((10,), {}, 10)),
    ('Rul4', Rul(Raw(abc), lambda x: int(x, 16), name='A'),
                              'd',      0, FAIL, None),

    ('Grm0', Grm({'Start': abc}), 'a',  0, 1,    _noatom),
    ('Grm1', Grm({'Start': abc}), 'd',  0, FAIL, None),
    ('Grm1', Grm({'Start': Non('A'), 'A': abc}),
                                  'a',  0, 1,    _noatom),
]


@pytest.mark.parametrize('dfn,input,pos,end,match',
                         [row[1:] for row in data],
                         ids=[row[0] for row in data])
def test_exprs(dfn, input, pos, end, match):
    p = PackratParser(dfn)
    m = p.match(input, pos=pos, flags=pe.NONE)
    if match is None:
        assert m is None
    else:
        groups, groupdict, value = match
        assert m.end == end
        assert m.groups() == groups
        assert m.groupdict() == groupdict
        assert m.value() == value
