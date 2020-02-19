
from typing import List, NamedTuple, Any, Pattern

from pe import Error
from pe.constants import NOMATCH


class Match(NamedTuple):
    string: str
    pos: int
    endpos: int
    pe: 'Expression'
    matches: List['Match']

    def value(self) -> Any:
        string, pos, endpos, pe, matches = self
        matches = [m for m in matches if m.pe.capturing]
        if not matches:
            value = string[pos:endpos]
        else:
            value = [m.value() for m in matches]
        action = getattr(pe, 'action', None)
        if action:
            value = action(value)
        return value


class Expression:
    __slots__ = '_re', 'capturing',

    def __init__(self):
        self._re: Pattern = None
        self.capturing: bool = False

    def scan(self, s: str, pos: int = 0) -> int:
        if self._re is None:
            raise Error(
                'expression cannot be used for scanning')
        # TODO: walrus
        m = self._re.match(s, pos)
        if not m:
            return NOMATCH
        return m.end()

    def match(self, s: str, pos: int = 0) -> Match:
        if self.capturing:
            raise Error(
                'capturing expressions must implement a match() method')
        end = self.scan(s, pos=pos)
        if end < 0:
            return None
        else:
            return Match(s, pos, end, self, [])


class Term(Expression):
    """An atomic expression."""

    __slots__ = ()

    capturing = False

    def scan(self, s: str, pos: int = 0):
        # TODO: walrus
        m = self._re.match(s, pos)
        if not m:
            return NOMATCH
        return m.end()

    def match(self, s: str, pos: int = 0):
        end = self.scan(s, pos=pos)
        if end < 0:
            return None
        else:
            return Match(s, pos, end, self, [])
