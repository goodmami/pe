
import pytest

from pe.constants import FAIL, Operator
from pe.core import Grammar
from pe.packrat import (
    Regex,
    Sequence as Seq,
    Choice as Chc,
    Repeat as Rpt,
    Lookahead as Look,
    Bind,
    Rule,
    PackratParser as PrP,
)

abc = Regex('[abc]')
xyz = Regex('[xyz]')

abc_grm = Grammar(definitions={'Start': (Operator.CLS, 'abc')})

data = [
    #typ, args, kwargs,       input,   pos,scan, (groups, groupdict, value)
    (Regex, ('.'), {},        'aaa',    0, 1,    ((), {}, 'a')),
    (Regex, ('.'), {},        '   ',    0, 1,    ((), {}, ' ')),
    (Regex, ('.'), {},        '',       0, FAIL, None),

    (Regex, ('a',),   {},     'a',      0, 1,    ((), {}, 'a')),
    (Regex, ('a',),   {},     'aa',     0, 1,    ((), {}, 'a')),
    (Regex, ('a',),   {},     'b',      0, FAIL, None),
    (Regex, ('a',),   {},     'a',      1, FAIL, None),
    (Regex, ('a',),   {},     'ab',     1, FAIL, None),
    (Regex, ('b',),   {},     'ab',     0, FAIL, None),
    (Regex, ('b',),   {},     'ab',     1, 2,    ((), {}, 'b')),
    (Regex, ('abc',), {},     'abcabc', 0, 3,    ((), {}, 'abc')),
    (Regex, ('abc',), {},     'abcabc', 1, FAIL, None),
    (Regex, ('abc',), {},     'abcabc', 3, 6,    ((), {}, 'abc')),

    (Regex, ('[ab]',),  {},   'a',      0, 1,    ((), {}, 'a')),
    (Regex, ('[ab]',),  {},   'aa',     0, 1,    ((), {}, 'a')),
    (Regex, ('[ab]',),  {},   'b',      0, 1,    ((), {}, 'b')),
    (Regex, ('[ab]',),  {},   'a',      1, FAIL, None),
    (Regex, ('[ab]',),  {},   'ab',     1, 2,    ((), {}, 'b')),

    (Regex, ('a',),   {},     'a',      0, 1, ((), {}, 'a')),
    (Regex, ('a*',),  {},     'aaa',    0, 3, ((), {}, 'aaa')),
    (Regex, ('a|b',), {},     'b',      0, 1, ((), {}, 'b')),
    (Regex, ('(?:a)(b)(?:c)(d)',), {},
                              'abcd',   0, 4, (('b', 'd'), {}, 'b')),

    (Seq, (abc,),     {},     'aaa',   0, 1,     ((), {}, 'a')),
    (Seq, (abc, abc), {},     'bbb',   0, 2,     ((), {}, 'bb')),
    (Seq, (abc,),     {},     'd',     0, FAIL,  None),

    (Chc, (abc,),     {},     'aaa',   0, 1,     ((), {}, 'a')),
    (Chc, (abc, abc), {},     'aaa',   0, 1,     ((), {}, 'a')),
    (Chc, (abc, xyz), {},     'yyy',   0, 1,     ((), {}, 'y')),
    (Chc, (abc, xyz), {},     'd',     0, FAIL,  None),

    (Rpt, (abc,), {},         '',      0, 0,     ((), {}, '')),
    (Rpt, (abc,), {'min': 1}, '',      0, FAIL,  None),
    (Rpt, (abc,), {},         'aabbc', 0, 5,     ((), {}, 'aabbc')),
    (Rpt, (abc,), {'max': 3}, 'aabbc', 0, 3,     ((), {}, 'aab')),

    (Look, (abc, True), {},   'a',     0, 0,     ((), {}, '')),
    (Look, (abc, True), {},   'd',     0, FAIL,  None),

    (Look, (abc, False), {},  'a',     0, FAIL,  None),
    (Look, (abc, False), {},  'd',     0, 0,     ((), {}, '')),

    (Bind, (abc,), {},        'a',     0, 1,     ((), {}, None)),
    (Bind, (abc,), {},        'd',     0, FAIL,  None),
    (Bind, (abc,), {'name': 'x'},
                              'a',     0, 1,     ((), {'x': 'a'}, None)),

    (Rule, (abc,), {},        'a',     0, 1,     ((), {}, 'a')),
    (Rule, (abc,), {},        'd',     0, FAIL,  None),
    (Rule, (abc,), {'action': lambda x: int(x, 16)},
                              'a',     0, 1,     ((10,), {}, 10)),
    (Rule, (abc,), {'action': lambda x: int(x, 16)},
                              'd',     0, FAIL,  None),

    (PrP, (abc_grm), {},      'a',     0, 1,     ((), {}, 'a')),
    (PrP, (abc_grm), {},      'd',     0, FAIL,  None),
]


@pytest.mark.parametrize('type,args,kwargs,input,pos,scan,match', data)
def test_exprs(type, args, kwargs, input, pos, scan, match):
    e = type(*args, **kwargs)
    assert e.scan(input, pos=pos) == scan
    m = e.match(input, pos=pos)
    if match is None:
        assert m is None
    else:
        groups, groupdict, value = match
        assert m.end == scan
        assert m.groups() == groups
        assert m.groupdict() == groupdict
        assert m.value() == value


def test_invalid_Repeat():
    with pytest.raises(ValueError):
        Rpt(abc, min=-1)
    with pytest.raises(ValueError):
        Rpt(abc, max=-2)
    with pytest.raises(ValueError):
        Rpt(abc, min=2, max=1)
