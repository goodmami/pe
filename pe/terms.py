
from typing import Union
import re

from pe.core import Term


class Dot(Term):
    def __init__(self):
        self._re = re.compile('.')


class Literal(Term):
    __slots__ = 'string',

    def __init__(self, string: str):
        self.string = string
        self._re = re.compile(re.escape(string))


class Class(Term):
    __slots__ = 'clsstr', 'negated',

    def __init__(self, clsstr: str, negate: bool = False):
        self.clsstr = clsstr
        self.negated = negate
        neg = '^' if negate else ''
        cls = clsstr.replace('[', '\\[').replace(']', '\\]')
        self._re = re.compile(f'[{neg}{cls}]')


class Regex(Term):
    def __init__(self,
                 pattern: Union[str, re.Pattern],
                 flags: int = 0):
        if isinstance(pattern, re.Pattern):
            self._re = pattern
        else:
            self._re = re.compile(pattern, flags=flags)
