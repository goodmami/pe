
import pe
from pe.operators import (
    Regex,
    Sequence,
    Nonterminal,
    Discard
)
from pe._grammar import Grammar
from pe._parse import loads
from pe._optimize import optimize


def iload(s): return optimize(loads(s), inline=True, regex=False)
def rload(s): return optimize(loads(s), inline=False, regex=True)
def grm(d): return Grammar(definitions=d, start=next(iter(d)))


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
                      flags=pe.NONE).match('ab').value() == ('a', 'b')
    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=pe.INLINE).match('ab').value() == ('a', 'b')


def test_regex():
    assert (rload(r'A <- "a"') ==
            grm({'A': Regex(r'a')}))
    assert (rload(r'A <- "a" [bc]') ==
            grm({'A': Sequence(Regex(r'a'), Regex(r'[bc]'))}))
    assert (rload(r'A <- :("a" [bc])') ==
            grm({'A': Discard(Regex(r'a[bc]'))}))
    assert (rload(r'A <- "a" B  B <- [bc]') ==
            grm({'A': Sequence(Regex('a'), Nonterminal('B')),
                 'B': Regex('[bc]')}))
    assert (rload(r'A <- "a"* [bc]+') ==
            grm({'A': Sequence(Regex(r'(?=(?P<_1>(?:a)*))(?P=_1)'),
                               Regex(r'(?=(?P<_2>(?:[bc])+))(?P=_2)'))}))
    assert (rload(r'A <- "a" :([bc] / "d")*') ==
            grm({'A': Sequence(
                Regex(r'a'),
                Discard(Regex(r'(?=(?P<_2>(?:(?=(?P<_1>[bc]|d))(?P=_1))*))(?P=_2)')))}))

    assert pe.compile('A <- "a" "b"',
                      flags=pe.NONE).match('ab').value() == ('a', 'b')
    assert pe.compile('A <- "a" "b"',
                      flags=pe.REGEX).match('ab').value() == ('a', 'b')
    assert pe.compile('A <- "a" :"b" "c"',
                      flags=pe.NONE).match('abc').value() == ('a', 'c')
    assert pe.compile('A <- "a" :"b" "c"',
                      flags=pe.REGEX).match('abc').value() == ('a', 'c')


def test_regex_not_dot():
    assert (rload(r'A <- !"a" .')   == grm({'A': Regex(r'[^a]')}))
    assert (rload(r'A <- !"\\" .')  == grm({'A': Regex(r'[^\\]')}))
    assert (rload(r'A <- ![\\] .')  == grm({'A': Regex(r'[^\\]')}))
    assert (rload(r'A <- ![abc] .') == grm({'A': Regex(r'[^abc]')}))
    assert (rload(r'A <- (![abc] .)*') ==
            grm({'A': Regex(r'(?=(?P<_1>(?:[^abc])*))(?P=_1)')}))

