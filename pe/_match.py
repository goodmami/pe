
from typing import Union, List, Dict, Any
import textwrap

from pe._constants import Value
from pe._definition import Definition


class Match:
    """The result of a parsing expression match."""

    __slots__ = 'string', 'pos', 'end', 'pe', '_args', '_kwargs'

    def __init__(self,
                 string: str,
                 pos: int,
                 end: int,
                 pe: Definition,
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

    def group(self, key_or_index: Union[str, int] = 0) -> Any:
        if not isinstance(key_or_index, (str, int)):
            raise TypeError(type(key_or_index))
        if key_or_index == 0:
            return self.string[self.pos:self.end]
        elif isinstance(key_or_index, int):
            index = key_or_index - 1
            if index < 0 or index >= len(self._args):
                raise IndexError('no such group')
            return self._args[index]
        else:
            if key_or_index not in self._kwargs:
                raise IndexError('no such group')
            return self._kwargs[key_or_index]

    def groups(self):
        return tuple(self._args or ())

    def groupdict(self):
        return dict(self._kwargs or ())

    def value(self):
        return evaluate(self._args, self.pe.value)


def evaluate(args, value: Value):
    if value == Value.ITERABLE:
        return args
    elif value == Value.ATOMIC:
        return args[0]
    elif value == Value.EMPTY:
        return None
    else:
        raise Error(f'invalid value type: {value!r}')
