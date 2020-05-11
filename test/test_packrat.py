
import pytest

import pe
from pe._constants import FAIL
from pe.operators import (
    Dot,
    Literal as Lit,
    Class as Cls,
    Regex as Rgx,
    # Nonterminal as Non,
    Optional as Opt,
    Star as Str,
    Plus as Pls,
    And,
    Not,
    Bind as Bnd,
    Capture as Cap,
    Sequence as Seq,
    Choice as Chc,
    Rule as Rul,
)
from pe._grammar import Grammar
from pe.actions import Pack
from pe.packrat import PackratParser


# don't reuse these in value-changing operations like Bind
abc = Cls('abc')
xyz = Cls('xyz')
abseq = Seq('a', 'b')

_blank = ((), {}, None)

data = [  # noqa: E127
    # id     definition       input,  start,end, (groups, groupdict, value)
    ('Dot0', Dot(),           'aaa',    0, 1,    _blank),
    ('Dot1', Dot(),           '   ',    0, 1,    _blank),
    ('Dot2', Dot(),           '',       0, FAIL, None),

    ('Lit0', Lit('a',),       'a',      0, 1,    _blank),
    ('Lit1', Lit('a',),       'aa',     0, 1,    _blank),
    ('Lit2', Lit('a',),       'b',      0, FAIL, None),
    ('Lit3', Lit('a',),       'a',      1, FAIL, None),
    ('Lit4', Lit('a',),       'ab',     1, FAIL, None),
    ('Lit5', Lit('b',),       'ab',     0, FAIL, None),
    ('Lit6', Lit('b',),       'ab',     1, 2,    _blank),
    ('Lit7', Lit('abc',),     'abcabc', 0, 3,    _blank),
    ('Lit8', Lit('abc',),     'abcabc', 1, FAIL, None),
    ('Lit9', Lit('abc',),     'abcabc', 3, 6,    _blank),

    ('Cls0', Cls('[ab]',),    'a',      0, 1,    _blank),
    ('Cls1', Cls('[ab]',),    'aa',     0, 1,    _blank),
    ('Cls2', Cls('[ab]',),    'b',      0, 1,    _blank),
    ('Cls3', Cls('[ab]',),    'a',      1, FAIL, None),
    ('Cls4', Cls('[ab]',),    'ab',     1, 2,    _blank),

    ('Rgx0', Rgx('a*'),       'aaa',    0, 3,    _blank),
    ('Rgx1', Rgx('a|b',),     'b',      0, 1,    _blank),
    ('Rgx2', Rgx('(?:a)(b)(?:c)(d)',),
                              'abcd',   0, 4,    _blank),

    ('Opt0', Opt(abc),        'd',      0, 0,    _blank),
    ('Opt1', Opt(abc),        'ab',     0, 1,    _blank),
    ('Opt2', Opt(abseq),      'd',      0, 0,    _blank),
    ('Opt3', Opt(abseq),      'ab',     0, 2,    _blank),

    ('Str0', Str(abc),        '',       0, 0,    _blank),
    ('Str1', Str(abc),        'aabbc',  0, 5,    _blank),

    ('Pls0', Pls(abc,),       '',       0, FAIL, None),
    ('Pls1', Pls(abc,),       'aabbc',  0, 5,    _blank),

    ('And0', And(abc),        'a',      0, 0,    _blank),
    ('And1', And(abc),        'd',      0, FAIL, None),

    ('Not0', Not(abc),        'a',      0, FAIL, None),
    ('Not1', Not(abc),        'd',      0, 0,    _blank),

    ('Bnd0', Bnd(Cls('abc'), name='x'),
                              'a',      0, 1,    ((), {'x': None}, None)),

    ('Seq0', Seq(abc),        'aaa',    0, 1,    _blank),
    ('Seq1', Seq(abc, abc),   'bbb',    0, 2,    _blank),
    ('Seq2', Seq(abc),        'd',      0, FAIL, None),

    ('Chc0', Chc(abc),        'aaa',    0, 1,    _blank),
    ('Chc1', Chc(abc, abc),   'aaa',    0, 1,    _blank),
    ('Chc2', Chc(abc, xyz),   'yyy',    0, 1,    _blank),
    ('Chc3', Chc(abc, xyz),   'd',      0, FAIL, None),

    ('Cap1', Cap(Dot()),      'abc',    0, 1,    (('a',), {}, 'a')),
    ('Cap2', Cap(abc),        'cba',    0, 1,    (('c',), {}, 'c')),
    ('Cap3', Str(Cap(abc)),   'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                                  {},
                                                  'a')),
    ('Cap4', Cap(Str(abc)),   'aabbc',  0, 5,    (('aabbc',), {}, 'aabbc')),
    ('Cap5', Seq(Cap(abc), Cls('xyz'), Cap(abc)),
                              'axb',    0, 3,    (('a', 'b'), {}, 'a')),

    ('Rul0', Rul(abc, None),  'a',      0, 1,    _blank),
    ('Rul1', Rul(Cap(abc), None), 'a',  0, 1,    (('a',), {}, 'a')),
    ('Rul2', Rul(abc, None),  'd',      0, FAIL, None),
    ('Rul3', Rul(Cap(abc), lambda x: int(x, 16), name='A'),
                              'a',      0, 1,    ((10,), {}, 10)),
    ('Rul4', Rul(Cap(abc), lambda x: int(x, 16), name='A'),
                              'd',      0, FAIL, None),
    ('Rul5', Rul(Seq(Cap('a'), Cap('b')), action=Pack(list)),
                              'ab',     0, 2,    ((['a', 'b'],),
                                                  {},
                                                  ['a', 'b'])),
]


@pytest.mark.parametrize('dfn,input,pos,end,match',
                         [row[1:] for row in data],
                         ids=[row[0] for row in data])
def test_exprs(dfn, input, pos, end, match):
    g = Grammar({'Start': dfn})
    p = PackratParser(g)
    m = p.match(input, pos=pos, flags=pe.NONE)
    if match is None:
        assert m is None
    else:
        groups, groupdict, value = match
        assert m.end() == end
        assert m.groups() == groups
        assert m.groupdict() == groupdict
        assert m.value() == value
