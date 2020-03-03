
from typing import Union, List, Dict, Tuple, Callable

from pe.constants import FAIL, Operator


class Error(Exception):
    """Exception raised for invalid parsing expressions."""


class Match:
    __slots__ = 'string', 'pos', 'end', 'pe', '_args', '_kwargs'

    def __init__(self,
                 string: str,
                 pos: int,
                 end: int,
                 pe: 'Expression',
                 args: List = None,
                 kwargs: Dict = None):
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
        if self._args is None:
            return self.string[self.pos:self.end]
        elif self._args:
            return self._args[0]
        return None


class Expression:
    __slots__ = 'structured',

    def __init__(self, structured: bool = True):
        self.structured = structured

    def scan(self, s: str, pos: int = 0) -> int:
        raise NotImplementedError()

    def match(self, s: str, pos: int = 0) -> Union[Match, None]:
        raise NotImplementedError()


Definition = Union[Tuple[Operator],                          # DOT
                   Tuple[Operator, str],                     # LIT, CLS, NAM
                   Tuple[Operator, str, int],                # RGX
                   Tuple[Operator, str, 'Definition'],       # DEF, BND
                   Tuple[Operator, 'Definition'],            # AND, NOT
                   Tuple[Operator, 'Definition', Callable],  # RUL
                   Tuple[Operator, List['Definition']],      # SEQ, CHC
                   Tuple[Operator, 'Definition', int, int]]  # RPT



class Grammar:
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
