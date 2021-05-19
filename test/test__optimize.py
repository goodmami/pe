
import pe
from pe.operators import (
    Class,
    Regex,
    Sequence,
    Nonterminal,
    Capture,
)
from pe._grammar import Grammar
from pe._parse import loads
from pe._optimize import optimize


def gload(s, inline=False, common=False, regex=False):
    start, defmap = loads(s)
    return optimize(Grammar(defmap, start=start),
                    inline=inline,
                    common=common,
                    regex=regex)


def iload(s):
    return gload(s, inline=True)


def cload(s):
    return gload(s, common=True)


def rload(s, common=False):
    return gload(s, common=common, regex=True)


def grm(d):
    return Grammar(definitions=d, start=next(iter(d)))


def test_inline():
    assert (iload(r'A <- "a"') ==
            gload(r'A <- "a"'))
    assert (iload(r'A <- B  B <- "a"') ==
            gload(r'A <- "a" B <- "a"'))
    assert (iload(r'A <- B  B <- C  C <- "a"') ==
            gload(r'A <- "a"  B <- "a"  C <- "a"'))
    assert (iload(r'A <- "a" A') ==
            gload(r'A <- "a" A'))
    assert (iload(r'A <- "a" B  B <- A') ==
            gload(r'A <- "a" A  B <- "a" B'))
    assert (iload(r'A <- "a" B  B <- "b" A') ==
            gload(r'A <- "a" "b" A  B <- "b" "a" B'))

    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=pe.NONE).match('ab').value() is None
    assert pe.compile('A <- "a" B  B <- "b"',
                      flags=pe.INLINE).match('ab').value() is None
    assert pe.compile('A <- "a" B  B <- ~"b"',
                      flags=pe.NONE).match('ab').value() == 'b'
    assert pe.compile('A <- "a" B  B <- ~"b"',
                      flags=pe.INLINE).match('ab').value() == 'b'


def test_common():
    assert (cload(r'A <- "a"') ==
            gload(r'A <- "a"'))
    assert (cload(r'A <- !"a"') ==
            gload(r'A <- !"a"'))
    assert (cload(r'A <- !"a"') ==
            gload(r'A <- !"a"'))
    # add "b" to avoid dropping the sequence
    assert (cload(r'A <- !"a" . "b"') ==
            cload(r'A <- ![a] . "b"') ==
            grm({'A': Sequence(Class('a', negate=True), Literal('b'))}))
def test_regex():
    assert (rload(r'A <- "a"') ==
            grm({'A': Regex(r'a')}))
    assert (rload(r'A <- "a" [bc]') ==
            grm({'A': Regex(r'a[bc]')}))
    assert (rload(r'A <- ~("a" [bc])') ==
            grm({'A': Capture(Regex(r'a[bc]'))}))
    assert (rload(r'A <- "a" B  B <- [bc]') ==
            grm({'A': Sequence(Regex('a'), Nonterminal('B')),
                 'B': Regex('[bc]')}))
    assert (rload(r'A <- "a"* [bc]+') ==
            grm({'A': Regex(
                r'(?=(?P<_1>(?:a)*))(?P=_1)(?=(?P<_2>(?:[bc])+))(?P=_2)')}))
    assert (rload(r'A <- "a" ~([bc] / "d")*') ==
            grm({'A': Sequence(
                Regex(r'a'),
                Capture(Regex(
                    r'(?=(?P<_2>(?:(?=(?P<_1>[bc]|d))(?P=_1))*))(?P=_2)')))}))


def test_regex_values():
    assert pe.compile('A <- "a" "b"',
                      flags=pe.NONE).match('ab').value() is None
    assert pe.compile('A <- "a" "b"',
                      flags=pe.REGEX).match('ab').value() is None
    assert pe.compile('A <- "a" ~"b" "c"',
                      flags=pe.NONE).match('abc').value() == 'b'
    assert pe.compile('A <- "a" ~"b" "c"',
                      flags=pe.REGEX).match('abc').value() == 'b'


def test_regex_not_dot():
    assert (rload(r'A <- !"a" .')
            == grm({'A': Regex(r'(?!a)(?s:.)')}))
    assert (rload(r'A <- !"a" .', common=True)
            == grm({'A': Regex(r'[^a]')}))
    assert (rload(r'A <- !"\\" .', common=True)
            == grm({'A': Regex(r'[^\\]')}))
    assert (rload(r'A <- ![\\] .', common=True)
            == grm({'A': Regex(r'[^\\]')}))
    assert (rload(r'A <- ![abc] .', common=True)
            == grm({'A': Regex(r'[^abc]')}))
    assert (rload(r'A <- (![abc] .)*', common=True)
            == grm({'A': Regex(r'(?=(?P<_1>(?:[^abc])*))(?P=_1)')}))
