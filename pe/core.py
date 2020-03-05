
from typing import Union, List, Dict, Tuple, Callable, NamedTuple, Any

from pe.constants import FAIL, Operator


class Error(Exception):
    """Exception raised for invalid parsing expressions."""


class Match:
    """The result of a parsing expression match."""

    __slots__ = 'string', 'pos', 'end', 'pe', '_args', '_kwargs'

    def __init__(self,
                 string: str,
                 pos: int,
                 end: int,
                 pe: 'Expression',
                 args: List,
                 kwargs: Dict):
        self.string = string
        self.pos = pos
        self.end = end
        self.pe = pe
        self._args = args
        self._kwargs = kwargs

    def __repr__(self):
        return f'<Match object of: {self.pe!s} >'

    def groups(self):
        return tuple(self._args or ())

    def groupdict(self):
        return dict(self._kwargs or ())

    def value(self):
        if self.pe.iterable:
            return self._args
        elif self._args:
            return self._args[-1]
        else:
            return None


class Expression:
    """A compiled parsing expression."""

    __slots__ = 'iterable',

    def scan(self, s: str, pos: int = 0) -> int:
        raise NotImplementedError()

    def match(self, s: str, pos: int = 0) -> Union[Match, None]:
        raise NotImplementedError()


class Definition(NamedTuple):
    """An abstract definition of a parsing expression."""
    op: Operator
    args: Tuple[Any, ...]


class Grammar:
    """A parsing expression grammar definition."""

    def __init__(self,
                 definitions: Dict[str, Definition] = None,
                 actions: Dict[str, Callable] = None,
                 start: str = 'Start'):
        self.start = start
        self.definitions = definitions or {}
        self.actions = actions or {}

    def __setitem__(self, name: str, definition: Definition):
        self.definitions[name] = definition

    def __getitem__(self, name):
        return self.definitions[name]
