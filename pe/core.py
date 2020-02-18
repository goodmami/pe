
from typing import List, NamedTuple
import re

from pe.constants import NOMATCH


class Matcher:
    def match(self, s: str, pos: int = 0):
        raise NotImplementedError


class Match(NamedTuple):
    string: str
    pos: int
    endpos: int
    matcher: Matcher
    matches: List['Match']

    def value(self):
        string, pos, endpos, matcher, matches = self
        print()
        print(tuple(self))
        if not matches:
            value = string[pos:endpos]
        else:
            value = [m.value() for m in matches]
        action = getattr(self.matcher, 'action', None)
        if action:
            print('DO', action)
            value = action(value)
        return value


class Scanner(Matcher):
    __slots__ = '_re',

    capturing = False

    def __init__(self):
        self._re: re.Pattern = None

    def __call__(self, s: str, pos: int = 0):
        # TODO: walrus
        m = self._re.match(s, pos)
        if not m:
            return NOMATCH
        return m.end()

    def match(self, s: str, pos: int = 0):
        end = self(s, pos=pos)
        if end == NOMATCH:
            return None
        else:
            return Match(s, pos, end, self, [])


class Combinator(Matcher):

    __slots__ = 'capturing',

    def __init__(self):
        self.capturing: bool = False

    def match(self, s: str, pos: int = 0):
        pass
