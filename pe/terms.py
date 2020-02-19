
from typing import Union, Pattern
import re

from pe.core import Term


class Dot(Term):
    def __init__(self):
        self._re = re.compile('.')

    def __str__(self):
        return 'Dot()'


class Literal(Term):
    __slots__ = 'string',

    def __init__(self, string: str):
        self.string = string
        self._re = re.compile(re.escape(string))

    def __str__(self):
        return f'Literal({self.string!r})'


class Class(Term):
    __slots__ = 'clsstr', 'negated',

    def __init__(self, clsstr: str, negate: bool = False):
        self.clsstr = clsstr
        self.negated = negate
        neg = '^' if negate else ''
        cls = clsstr.replace('[', '\\[').replace(']', '\\]')
        self._re = re.compile(f'[{neg}{cls}]')

    def __str__(self):
        if self.negated:
            return f'Class({self.clsstr!r}, negate=True)'
        else:
            return f'Class({self.clsstr!r})'


class Regex(Term):
    def __init__(self,
                 pattern: Union[str, Pattern],
                 flags: int = 0):
        # re.compile() works even if the pattern is a regex object
        self._re = re.compile(pattern, flags=flags)

    def __str__(self):
        return f'Regex({self.pattern!r}, flags={self.flags})'
