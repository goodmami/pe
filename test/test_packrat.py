
import pytest

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
    Discard as Dis,
    Raw,
    Sequence as Seq,
    Choice as Chc,
    Rule as Rul,
)
from pe._grammar import Grammar as Grm
from pe.packrat import PackratParser


# don't reuse these in value-changing operations like Discard or Bind
abc = Cls('abc')
xyz = Cls('xyz')
abseq = Seq('a', 'b')

data = [
    #id      definition       input,   pos,scan, (groups, groupdict, value)
    ('Dot0', Dot(),           'aaa',    0, 1,    (('a',), {}, 'a')),
    ('Dot1', Dot(),           '   ',    0, 1,    ((' ',), {}, ' ')),
    ('Dot2', Dot(),           '',       0, FAIL, None),

    ('Lit0', Lit('a',),       'a',      0, 1,    (('a',), {}, 'a')),
    ('Lit1', Lit('a',),       'aa',     0, 1,    (('a',), {}, 'a')),
    ('Lit2', Lit('a',),       'b',      0, FAIL, None),
    ('Lit3', Lit('a',),       'a',      1, FAIL, None),
    ('Lit4', Lit('a',),       'ab',     1, FAIL, None),
    ('Lit5', Lit('b',),       'ab',     0, FAIL, None),
    ('Lit6', Lit('b',),       'ab',     1, 2,    (('b',), {}, 'b')),
    ('Lit7', Lit('abc',),     'abcabc', 0, 3,    (('abc',), {}, 'abc')),
    ('Lit8', Lit('abc',),     'abcabc', 1, FAIL, None),
    ('Lit9', Lit('abc',),     'abcabc', 3, 6,    (('abc',), {}, 'abc')),

    ('Cls0', Cls('[ab]',),    'a',      0, 1,    (('a',), {}, 'a')),
    ('Cls1', Cls('[ab]',),    'aa',     0, 1,    (('a',), {}, 'a')),
    ('Cls2', Cls('[ab]',),    'b',      0, 1,    (('b',), {}, 'b')),
    ('Cls3', Cls('[ab]',),    'a',      1, FAIL, None),
    ('Cls4', Cls('[ab]',),    'ab',     1, 2,    (('b',), {}, 'b')),

    ('Rgx0', Rgx('a*'),       'aaa',    0, 3,    (('aaa',), {}, 'aaa')),
    ('Rgx1', Rgx('a|b',),     'b',      0, 1,    (('b',), {}, 'b')),
    ('Rgx2', Rgx('(?:a)(b)(?:c)(d)',),
                              'abcd',   0, 4,    (('abcd',), {}, 'abcd')),

    ('Opt0', Opt(abc),        'd',      0, 0,    ((), {}, ())),
    ('Opt1', Opt(abc),        'ab',     0, 1,    (('a',), {}, ('a',))),
    ('Opt2', Opt(abseq),      'd',      0, 0,    ((), {}, ())),
    ('Opt3', Opt(abseq),      'ab',     0, 2,    (('a', 'b'), {}, ('a', 'b'))),

    ('Str0', Str(abc),        '',       0, 0,    ((), {}, ())),
    ('Str1', Str(abc),        'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                                  {},
                                                  ('a', 'a', 'b', 'b', 'c',))),

    ('Pls0', Pls(abc,),       '',       0, FAIL, None),
    ('Pls1', Pls(abc,),       'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                                  {},
                                                  ('a', 'a', 'b', 'b', 'c',))),

    ('And0', And(abc),        'a',      0, 0,    ((), {}, None)),
    ('And1', And(abc),        'd',      0, FAIL, None),

    ('Not0', Not(abc),        'a',      0, FAIL, None),
    ('Not1', Not(abc),        'd',      0, 0,    ((), {}, None)),

    ('Dis0', Dis(Cls('abc')), 'a',      0, 1,    ((), {}, None)),
    ('Dis1', Dis(Cls('abc')), 'd',      0, FAIL, None),
    ('Seq2', Seq(abc, Dis(Cls('xyz')), abc),
                              'axb',    0, 3,    (('a', 'b'), {}, ('a', 'b'))),

    ('Bnd0', Bnd(Cls('abc'), name='x'),
                              'a',   0, 1,    ((), {'x': 'a'}, None)),

    ('Seq0', Seq(abc),        'aaa',    0, 1,    (('a',), {}, 'a')),
    ('Seq1', Seq(abc, abc),   'bbb',    0, 2,    (('b', 'b',),
                                                  {},
                                                  ('b', 'b'))),
    ('Seq2', Seq(abc),        'd',      0, FAIL, None),

    ('Chc0', Chc(abc),        'aaa',    0, 1,    (('a',), {}, 'a')),
    ('Chc1', Chc(abc, abc),   'aaa',    0, 1,    (('a',), {}, ('a',))),
    ('Chc2', Chc(abc, xyz),   'yyy',    0, 1,    (('y',), {}, ('y',))),
    ('Chc3', Chc(abc, xyz),   'd',      0, FAIL, None),

    ('Rul0', Rul(abc, None),  'a',      0, 1,    (('a',), {}, 'a')),
    ('Rul1', Rul(abc, None),  'd',      0, FAIL, None),
    ('Rul2', Rul(abc, lambda x: int(x, 16), name='A'),
                              'a',      0, 1,    ((10,), {}, 10)),
    ('Rul3', Rul(abc, lambda x: int(x, 16), name='A'),
                              'd',      0, FAIL, None),

    ('Grm0', Grm({'Start': abc}), 'a',  0, 1,    (('a',), {}, 'a')),
    ('Grm1', Grm({'Start': abc}), 'd',  0, FAIL, None),
]


@pytest.mark.parametrize('dfn,input,pos,end,match',
                         [row[1:] for row in data],
                         ids=[row[0] for row in data])
def test_exprs(dfn, input, pos, end, match):
    p = PackratParser(dfn)
    m = p.match(input, pos=pos)
    if match is None:
        assert m is None
    else:
        groups, groupdict, value = match
        assert m.end == end
        assert m.groups() == groups
        assert m.groupdict() == groupdict
        assert m.value() == value
