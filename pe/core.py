
from typing import List, Tuple, Any, Pattern

from pe.constants import NOMATCH
from pe._re import set_re


class Error(Exception):
    """Exception raised for invalid parsing expressions."""


class Match:
    __slots__ = 'string', 'pos', 'end', 'pe', '_value',

    def __init__(self,
                 string: str,
                 pos: int,
                 end: int,
                 pe: 'Expression',
                 _value: Any):
        self.string = string
        self.pos = pos
        self.end = end
        self.pe = pe
        self._value = _value

    def __repr__(self):
        return f'<Match object of: {self.pe!s} >'

    def groups(self) -> Tuple[Any]:
        return tuple(self._value)

    def value(self) -> Any:
        if not self.pe.structured:
            return self.string[self.pos:self.end]
        else:
            return self._value


class Expression:
    __slots__ = '_re', 'structured', 'filtered',

    def __init__(self, structured: bool = False, filtered: bool = False):
        self._re: Pattern = None
        self.structured = structured
        self.filtered = filtered
        set_re(self)

    def scan(self, s: str, pos: int = 0) -> int:
        if self._re is None:
            raise Error(
                f'expression cannot be used for scanning: {self}')
        # TODO: walrus
        m = self._re.match(s, pos)
        if not m:
            return NOMATCH
        return m.end()

    def match(self, s: str, pos: int = 0) -> Match:
        end, value = self._match(s, pos)
        if end == NOMATCH:
            return None
        return Match(s, pos, end, self, value)

    def _match(self, s: str, pos: int) -> Tuple[int, Any]:
        end = self.scan(s, pos=pos)
        if end < 0:
            return end, None
        return end, s[pos:end]


class Lookahead(Expression):
    """An expression that may match but consumes no input."""

    __slots__ = 'expression', 'polarity',

    def __init__(self, expression: Expression, polarity: bool):
        self.expression = expression
        self.polarity = polarity
        super().__init__()

    def __str__(self):
        return f'Lookahead({self.expression!s}, {self.polarity})'

    def _match(self, s: str, pos: int = 0):
        if self._re:
            m = self._re.match(s, pos)
            if m:
                return pos, ''
            return NOMATCH, None

        end, _ = self.expression._match(s, pos=pos)
        if self.polarity ^ (end < 0):
            return NOMATCH, None
        return pos, ''


class Term(Expression):
    """An atomic expression."""

    __slots__ = ()
    structured = False
    filtered = False

    def scan(self, s: str, pos: int = 0):
        # TODO: walrus
        m = self._re.match(s, pos)
        if not m:
            return NOMATCH
        return m.end()

    def _match(self, s: str, pos: int = 0):
        end = self.scan(s, pos=pos)
        if end < 0:
            return end, None
        return end, s[pos:end]
