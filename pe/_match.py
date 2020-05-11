
from typing import Union, Tuple, List, Dict, Any
import textwrap

from pe._definition import Definition


class Match:
    """The result of a parsing expression match."""

    __slots__ = 'string', '_pos', '_end', 'pe', '_args', '_kwargs'

    def __init__(self,
                 string: str,
                 pos: int,
                 end: int,
                 pe: Definition,
                 args: List,
                 kwargs: Dict):
        self.string = string
        self._pos = pos
        self._end = end
        self.pe = pe
        self._args = args
        self._kwargs = kwargs

    def __repr__(self):
        pos, end = self._pos, self._end
        string = self.string[pos:end]
        substr = textwrap.shorten(string, width=20, placeholder='...')
        return (f'<{type(self).__name__} object;'
                f' span=({pos}, {end}), match={substr!r}>')

    def start(self) -> int:
        return self._pos

    def end(self) -> int:
        return self._end

    def span(self) -> Tuple[int, int]:
        return (self._pos, self._end)

    def group(self, key_or_index: Union[str, int] = 0) -> Any:
        if not isinstance(key_or_index, (str, int)):
            raise TypeError(type(key_or_index))
        if key_or_index == 0:
            return self.string[self._pos:self._end]
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
        return determine(self._args)


def determine(args):
    if args:
        return args[0]
    else:
        return None
