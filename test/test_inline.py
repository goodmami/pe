
import pe
from pe.grammar import loads
from pe.inline import optimize

def iload(s): return optimize(loads(s))


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
