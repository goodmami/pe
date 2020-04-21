
import pytest

from pe._parse import loads

patterns = [
    '.',
    '"a"',
    r'"\""',
    '[a]',
    '[a-z]',
    r'[\[\]]',
    'A',
    '"a"?',
    'A*',
    '[a]+',
    '&A',
    '!A',
    '~A',
    'a:A',
    'A B',
    'A / B',
    'A (B / C)',
    '(A B)+',
    '&A*',
    '(~A)*',
    'A (B / (~C)?)',
]


@pytest.mark.parametrize('pat', patterns)
def test_format(pat):
    start, defmap = loads(pat)
    defn = defmap[start]
    assert str(defn) == pat
