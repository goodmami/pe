
from typing import Union, List, Dict, Tuple, Callable, NamedTuple, Any
import textwrap

from pe._constants import FAIL, Operator, Value, Flag


class Error(Exception):
    """Exception raised for invalid parsing expressions."""


class ParseError(Error):

    def __init__(self,
                 message: str = None,
                 filename: str = None,
                 lineno: int = None,
                 offset: int = None,
                 text: str = None):
        self.message = message
        self.filename = filename
        self.lineno = lineno
        self.offset = offset
        self.text = text

    def __str__(self):
        parts = []
        if self.filename is not None:
            parts.append(f'File "{self.filename}"')
        if self.lineno is not None:
            parts.append(f'line {self.lineno}')
        if parts:
            parts = ['', '  ' + ', '.join(parts)]
        if self.text is not None:
            parts.append('    ' + self.text)
            if self.offset is not None:
                parts.append('    ' + (' ' * self.offset) + '^')
        elif parts:
            parts[-1] += f', character {self.offset}'
        if self.message is not None:
            name = self.__class__.__name__
            parts.append(f'{name}: {self.message}')
        return '\n'.join(parts)


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
        pos, end = self.pos, self.end
        string = self.string[pos:end]
        substr = textwrap.shorten(string, width=20, placeholder='...')
        return (f'<{type(self).__name__} object;'
                f' span=({pos}, {end}), match={substr!r}>')

    def groups(self):
        return tuple(self._args or ())

    def groupdict(self):
        return dict(self._kwargs or ())

    def value(self):
        return evaluate(self._args, self.pe.value_type)


class Expression:
    """A compiled parsing expression."""

    __slots__ = 'value_type',

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        raise NotImplementedError()


def evaluate(args, value_type: Value):
    if value_type == Value.ITERABLE:
        return args
    elif value_type == Value.ATOMIC:
        return args[0]
    elif value_type == Value.EMPTY:
        return None
    else:
        raise Error(f'invalid value type: {value_type!r}')
