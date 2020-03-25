
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
    Grammar as Grm,
)
from pe.packrat import PackratParser


abc = Cls('abc')
xyz = Cls('xyz')
abseq = Seq('a', 'b')

data = [
    #definition          input,   pos,scan, (groups, groupdict, value)
    (Dot(),              'aaa',    0, 1,    (('a',), {}, 'a')),
    (Dot(),              '   ',    0, 1,    ((' ',), {}, ' ')),
    (Dot(),              '',       0, FAIL, None),

    (Lit('a',),          'a',      0, 1,    (('a',), {}, 'a')),
    (Lit('a',),          'aa',     0, 1,    (('a',), {}, 'a')),
    (Lit('a',),          'b',      0, FAIL, None),
    (Lit('a',),          'a',      1, FAIL, None),
    (Lit('a',),          'ab',     1, FAIL, None),
    (Lit('b',),          'ab',     0, FAIL, None),
    (Lit('b',),          'ab',     1, 2,    (('b',), {}, 'b')),
    (Lit('abc',),        'abcabc', 0, 3,    (('abc',), {}, 'abc')),
    (Lit('abc',),        'abcabc', 1, FAIL, None),
    (Lit('abc',),        'abcabc', 3, 6,    (('abc',), {}, 'abc')),

    (Cls('[ab]',),       'a',      0, 1,    (('a',), {}, 'a')),
    (Cls('[ab]',),       'aa',     0, 1,    (('a',), {}, 'a')),
    (Cls('[ab]',),       'b',      0, 1,    (('b',), {}, 'b')),
    (Cls('[ab]',),       'a',      1, FAIL, None),
    (Cls('[ab]',),       'ab',     1, 2,    (('b',), {}, 'b')),

    (Rgx('a*'),          'aaa',    0, 3,    (('aaa',), {}, 'aaa')),
    (Rgx('a|b',),        'b',      0, 1,    (('b',), {}, 'b')),
    (Rgx('(?:a)(b)(?:c)(d)',),
                         'abcd',   0, 4,    (('abcd',), {}, 'abcd')),

    (Opt(abc),           'd',      0, 0,    ((), {}, ())),
    (Opt(abc),           'ab',     0, 1,    (('a',), {}, ('a',))),
    (Opt(abseq),         'd',      0, 0,    ((), {}, ())),
    (Opt(abseq),         'ab',     0, 2,    (('a', 'b'), {}, ('a', 'b'))),

    (Str(abc),           '',       0, 0,    ((), {}, ())),
    (Str(abc),           'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                             {},
                                             ('a', 'a', 'b', 'b', 'c',))),

    (Pls(abc,),          '',       0, FAIL, None),
    (Pls(abc,),          'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                             {},
                                             ('a', 'a', 'b', 'b', 'c',))),

    (And(abc),           'a',      0, 0,    ((), {}, None)),
    (And(abc),           'd',      0, FAIL, None),

    (Not(abc),           'a',      0, FAIL, None),
    (Not(abc),           'd',      0, 0,    ((), {}, None)),

    (Dis(abc),           'a',      0, 1,    ((), {}, None)),
    (Dis(abc),           'd',      0, FAIL, None),
    (Seq(abc, Dis(xyz), abc),
                         'axb',    0, 3,    (('a', 'b'), {}, ('a', 'b'))),

    (Bnd(abc, name='x'), 'a',      0, 1,    ((), {'x': 'a'}, None)),

    (Seq(abc),           'aaa',    0, 1,    (('a',), {}, 'a')),
    (Seq(abc, abc),      'bbb',    0, 2,    (('b', 'b',),
                                             {},
                                             ('b', 'b'))),
    (Seq(abc),           'd',      0, FAIL, None),

    (Chc(abc),           'aaa',    0, 1,    (('a',), {}, 'a')),
    (Chc(abc, abc),      'aaa',    0, 1,    (('a',), {}, ('a',))),
    (Chc(abc, xyz),      'yyy',    0, 1,    (('y',), {}, ('y',))),
    (Chc(abc, xyz),      'd',      0, FAIL, None),

    (Rul(abc, None),     'a',      0, 1,    (('a',), {}, 'a')),
    (Rul(abc, None),     'd',      0, FAIL, None),
    (Rul(abc, lambda x: int(x, 16), name='A'),
                         'a',      0, 1,    ((10,), {}, 10)),
    (Rul(abc, lambda x: int(x, 16), name='A'),
                         'd',      0, FAIL, None),

    (Grm({'Start': abc}), 'a',     0, 1,    (('a',), {}, 'a')),
    (Grm({'Start': abc}), 'd',     0, FAIL, None),
]


@pytest.mark.parametrize('dfn,input,pos,end,match', data)
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
