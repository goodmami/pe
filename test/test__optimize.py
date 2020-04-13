
import pe
from pe._constants import Value
from pe.operators import (
    Regex,
    Sequence,
    Nonterminal,
    Raw,
)
from pe._grammar import Grammar
from pe._parse import loads
from pe._optimize import optimize


def iload(s):
    return optimize(loads(s), inline=True, regex=False)


def rload(s):
    return optimize(loads(s), inline=False, regex=True)


def grm(d):
    return Grammar(definitions=d, start=next(iter(d)))


def _rgx(pat, val):
    r = Regex(pat)
    r.value = val
    return r


def test_inline():
    assert (iload(r'A <- "a"') ==
            loads(r'A <- "a"'))
    assert (iload(r'A <- B  B <- "a"') ==
            loads(r'A <- "a" B <- "a"'))
    assert (iload(r'A <- B  B <- C  C <- "a"') ==
            loads(r'A <- "a"  B <- "a"  C <- "a"'))
    assert (iload(r'A <- "a" A') ==
            loads(r'A <- "a" A'))
    assert (iload(r'A <- "a" B  B <- A') ==
            loads(r'A <- "a" A  B <- "a" B'))
    assert (iload(r'A <- "a" B  B <- "b" A') ==
            loads(r'A <- "a" "b" A  B <- "b" "a" B'))

    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=pe.NONE).match('ab').value() == ()
    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=pe.INLINE).match('ab').value() == ()
    assert pe.compile('A <- "a" B  B <- ~"b"',
                      flags=pe.NONE).match('ab').value() == ('b',)
    assert pe.compile('A <- "a" B  B <- ~"b"',
                      flags=pe.INLINE).match('ab').value() == ('b',)


def test_regex():
    assert (rload(r'A <- "a"') ==
            grm({'A': _rgx(r'a', Value.EMPTY)}))
    assert (rload(r'A <- "a" [bc]') ==
            grm({'A': _rgx(r'a[bc]', Value.ITERABLE)}))
    assert (rload(r'A <- ~("a" [bc])') ==
            grm({'A': Raw(_rgx(r'a[bc]', Value.ITERABLE))}))
    assert (rload(r'A <- "a" B  B <- [bc]') ==
            grm({'A': Sequence(_rgx('a', Value.EMPTY), Nonterminal('B')),
                 'B': _rgx('[bc]', Value.EMPTY)}))
    assert (rload(r'A <- "a"* [bc]+') ==
            grm({'A': _rgx(
                r'(?=(?P<_1>(?:a)*))(?P=_1)(?=(?P<_2>(?:[bc])+))(?P=_2)',
                Value.ITERABLE)}))
    assert (rload(r'A <- "a" ~([bc] / "d")*') ==
            grm({'A': Sequence(
                _rgx(r'a', Value.EMPTY),
                Raw(_rgx(r'(?=(?P<_2>(?:(?=(?P<_1>[bc]|d))(?P=_1))*))(?P=_2)',
                         Value.ITERABLE)))}))


def test_regex_values():
    assert pe.compile('A <- "a" "b"',
                      flags=pe.NONE).match('ab').value() == ()
    assert pe.compile('A <- "a" "b"',
                      flags=pe.REGEX).match('ab').value() == ()
    assert pe.compile('A <- "a" ~"b" "c"',
                      flags=pe.NONE).match('abc').value() == ('b',)
    assert pe.compile('A <- "a" ~"b" "c"',
                      flags=pe.REGEX).match('abc').value() == ('b',)


def test_regex_not_dot():
    assert (rload(r'A <- !"a" .')
            == grm({'A': _rgx(r'[^a]', Value.ITERABLE)}))
    assert (rload(r'A <- !"\\" .')
            == grm({'A': _rgx(r'[^\\]', Value.ITERABLE)}))
    assert (rload(r'A <- ![\\] .')
            == grm({'A': _rgx(r'[^\\]', Value.ITERABLE)}))
    assert (rload(r'A <- ![abc] .')
            == grm({'A': _rgx(r'[^abc]', Value.ITERABLE)}))
    assert (rload(r'A <- (![abc] .)*')
            == grm({'A': _rgx(r'(?=(?P<_1>(?:[^abc])*))(?P=_1)',
                              Value.ITERABLE)}))
