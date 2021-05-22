
from typing import Union, List, Tuple
import re

from pe._constants import FAIL as FAILURE


class Scanner:
    def scan(self, s: str, pos: int = 0) -> int:
        try:
            return self._scan(s, pos, len(s))
        except IndexError:
            return FAILURE

    def _scan(self, s: str, pos: int, slen: int) -> int:
        return FAILURE


class Dot(Scanner):
    def _scan(self, s: str, pos: int, slen: int) -> int:
        if pos < slen:
            return pos + 1
        return FAILURE


class Literal(Scanner):

    def __init__(self, x: str):
        self._x = x
        self._xlen = len(x)

    def _scan(self, s: str, pos: int, slen: int) -> int:
        end = pos + self._xlen
        if s[pos:end] != self._x:
            return FAILURE
        return end

    def __repr__(self):
        return f'{self.__class__.__name__}({self._x!r})'


class CharacterClass(Scanner):

    def __init__(
        self,
        ranges: List[Tuple[str, Union[str, None]]],
        negate: bool = False,
        mincount: int = 1,
        maxcount: int = 1
    ):
        self._chars = ''.join(a for a, b in ranges if not b)
        self._ranges = ''.join(a+b for a, b in ranges if b)
        self._rangelen = len(self._ranges)
        self._negate = negate
        self.mincount = mincount
        self.maxcount = maxcount

    def _scan(self, s: str, pos: int, slen: int) -> int:
        ranges = self._ranges
        rangelen = self._rangelen
        mincount = self.mincount
        maxcount = self.maxcount
        i = 0
        while maxcount and pos < slen:
            c = s[pos]
            matched = c in self._chars
            while i < rangelen:
                if ranges[i] <= c <= ranges[i+1]:
                    matched = True
                    break
                i += 2
            if matched ^ self._negate:
                pos += 1
                maxcount -= 1
                mincount -= 1
            else:
                break
        if mincount > 0:
            return FAILURE
        return pos

    def __repr__(self):
        clsstr = (self._chars
                  + ''.join(f'{a}-{b}'
                            for a, b in zip(self._ranges[::2],
                                            self._ranges[1::2])))
        return (f'{self.__class__.__name__}({clsstr!r},'
                f' negate={self._negate},'
                f' mincount={self.mincount},'
                f' maxcount={self.maxcount})')


class Regex(Scanner):
    def __init__(self, pattern: str, flags: int = 0):
        self._regex = re.compile(pattern, flags=flags)

    def _scan(self, s: str, pos: int, slen: int) -> int:
        m = self._regex.match(s, pos=pos)
        if m is None:
            return FAILURE
        else:
            return m.end()
