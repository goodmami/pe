
from typing import List, Dict, Tuple, Any, Pattern

from pe.constants import NOMATCH
from pe._re import set_re


class Error(Exception):
    """Exception raised for invalid parsing expressions."""


class Match:
    __slots__ = 'string', 'pos', 'end', 'pe', '_args', '_kwargs'

    def __init__(self,
                 string: str,
                 pos: int,
                 end: int,
                 pe: 'Expression',
                 _args: List = None,
                 _kwargs: Dict = None):
        self.string = string
        self.pos = pos
        self.end = end
        self.pe = pe
        self._args = _args
        self._kwargs = _kwargs

    def __repr__(self):
        return f'<Match object of: {self.pe!s} >'

    def groups(self):
        return tuple(self._args or ())

    def groupdict(self):
        return dict(self._kwargs or ())


class Expression:
    __slots__ = '_re', 'structured', 'filtered',

    def __init__(self, structured: bool = False, filtered: bool = False):
        self._re: Pattern = None
        self.structured = structured
        self.filtered = filtered
        # set_re        (self)

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
        end, args, kwargs = self._match(s, pos)
        if end == NOMATCH:
            return None
        return Match(s, pos, end, self, args, kwargs)

    def _match(self, s: str, pos: int) -> Tuple[int, Any]:
        raise NotImplementedError()


class Lookahead(Expression):
    """An expression that may match but consumes no input."""

    __slots__ = 'expression', 'polarity',

    def __init__(self, expression: Expression, polarity: bool):
        self.expression = expression
        self.polarity = polarity
        super().__init__()

    def __repr__(self):
        clsname = type(self).__name__
        return f'{clsname}({self.expression!s}, {self.polarity})'

    def _match(self, s: str, pos: int):
        if self._re:
            m = self._re.match(s, pos)
            if m:
                return pos, None, None
            return NOMATCH, None, None

        end, _, _ = self.expression._match(s, pos)
        if self.polarity ^ (end < 0):
            return NOMATCH, None, None
        return pos, None, None


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

    def _match(self, s: str, pos: int):
        end = self.scan(s, pos=pos)
        if end < 0:
            return end, None, None
        return end, None, None
