
import pytest

from pe._constants import FAIL
from pe.grammar import Class, Grammar
from pe.packrat import (
    Terminal as Trm,
    Optional as Opt,
    Star,
    Plus,
    Lookahead as Look,
    Bind,
    Sequence as Seq,
    Choice as Chc,
    Rule,
    PackratParser as PrP,
)

abc = Trm('[abc]')
xyz = Trm('[xyz]')
abseq = Seq(Trm('a'), Trm('b'))

abc_grm = Grammar(definitions={'Start': Class('abc')})

data = [
    #typ, args, kwargs,       input,   pos,scan, (groups, groupdict, value)
    (Trm, ('.'), {},          'aaa',    0, 1,    (('a',), {}, 'a')),
    (Trm, ('.'), {},          '   ',    0, 1,    ((' ',), {}, ' ')),
    (Trm, ('.'), {},          '',       0, FAIL, None),

    (Trm, ('a',),   {},       'a',      0, 1,    (('a',), {}, 'a')),
    (Trm, ('a',),   {},       'aa',     0, 1,    (('a',), {}, 'a')),
    (Trm, ('a',),   {},       'b',      0, FAIL, None),
    (Trm, ('a',),   {},       'a',      1, FAIL, None),
    (Trm, ('a',),   {},       'ab',     1, FAIL, None),
    (Trm, ('b',),   {},       'ab',     0, FAIL, None),
    (Trm, ('b',),   {},       'ab',     1, 2,    (('b',), {}, 'b')),
    (Trm, ('abc',), {},       'abcabc', 0, 3,    (('abc',), {}, 'abc')),
    (Trm, ('abc',), {},       'abcabc', 1, FAIL, None),
    (Trm, ('abc',), {},       'abcabc', 3, 6,    (('abc',), {}, 'abc')),

    (Trm, ('[ab]',),  {},     'a',      0, 1,    (('a',), {}, 'a')),
    (Trm, ('[ab]',),  {},     'aa',     0, 1,    (('a',), {}, 'a')),
    (Trm, ('[ab]',),  {},     'b',      0, 1,    (('b',), {}, 'b')),
    (Trm, ('[ab]',),  {},     'a',      1, FAIL, None),
    (Trm, ('[ab]',),  {},     'ab',     1, 2,    (('b',), {}, 'b')),

    (Trm, ('a',),   {},       'a',      0, 1,    (('a',), {}, 'a')),
    (Trm, ('a*',),  {},       'aaa',    0, 3,    (('aaa',), {}, 'aaa')),
    (Trm, ('a|b',), {},       'b',      0, 1,    (('b',), {}, 'b')),
    (Trm, ('(?:a)(b)(?:c)(d)',), {},
                              'abcd',   0, 4,    (('abcd',), {}, 'abcd')),

    (Seq, (abc,),     {},     'aaa',    0, 1,    (('a',), {}, ('a',))),
    (Seq, (abc, abc), {},     'bbb',    0, 2,    (('b', 'b',),
                                                  {},
                                                  ('b', 'b'))),
    (Seq, (abc,),     {},     'd',      0, FAIL, None),

    (Chc, (abc,),     {},     'aaa',    0, 1,    (('a',), {}, ('a',))),
    (Chc, (abc, abc), {},     'aaa',    0, 1,    (('a',), {}, ('a',))),
    (Chc, (abc, xyz), {},     'yyy',    0, 1,    (('y',), {}, ('y',))),
    (Chc, (abc, xyz), {},     'd',      0, FAIL, None),

    (Opt, (abc,), {},         'd',      0, 0,    ((), {}, ())),
    (Opt, (abc,), {},         'ab',     0, 1,    (('a',), {}, ('a',))),
    (Opt, (abseq,), {},       'd',      0, 0,    ((), {}, ())),
    (Opt, (abseq,), {},       'ab',     0, 2,    (('a', 'b'), {}, ('a', 'b'))),

    (Star, (abc,), {},        '',       0, 0,    ((), {}, ())),
    (Star, (abc,), {},        'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                                  {},
                                                  ('a', 'a', 'b', 'b', 'c',))),

    (Plus, (abc,), {},        '',       0, FAIL, None),
    (Plus, (abc,), {},        'aabbc',  0, 5,    (('a', 'a', 'b', 'b', 'c',),
                                                  {},
                                                  ('a', 'a', 'b', 'b', 'c',))),

    (Look, (abc, True), {},   'a',      0, 0,    ((), {}, None)),
    (Look, (abc, True), {},   'd',      0, FAIL, None),

    (Look, (abc, False), {},  'a',      0, FAIL, None),
    (Look, (abc, False), {},  'd',      0, 0,    ((), {}, None)),

    (Bind, (abc,), {},        'a',      0, 1,    ((), {}, None)),
    (Bind, (abc,), {},        'd',      0, FAIL, None),
    (Bind, (abc,), {'name': 'x'},
                              'a',      0, 1,    ((), {'x': 'a'}, None)),
    (Seq, (abc, Bind(xyz), abc), {},
                              'axb',    0, 3,    (('a', 'b'), {}, ('a', 'b'))),

    (Rule, ('A', abc,), {},   'a',      0, 1,    (('a',), {}, 'a')),
    (Rule, ('A', abc,), {},   'd',      0, FAIL, None),
    (Rule, ('A', abc,), {'action': lambda x: int(x, 16)},
                              'a',      0, 1,    ((10,), {}, 10)),
    (Rule, ('A', abc,), {'action': lambda x: int(x, 16)},
                              'd',      0, FAIL, None),

    (PrP, (abc_grm,), {},     'a',      0, 1,    (('a',), {}, 'a')),
    (PrP, (abc_grm,), {},     'd',      0, FAIL, None),
]


@pytest.mark.parametrize('type,args,kwargs,input,pos,end,match', data)
def test_exprs(type, args, kwargs, input, pos, end, match):
    e = type(*args, **kwargs)
    m = e.match(input, pos=pos)
    if match is None:
        assert m is None
    else:
        groups, groupdict, value = match
        assert m.end == end
        assert m.groups() == groups
        assert m.groupdict() == groupdict
        assert m.value() == value
