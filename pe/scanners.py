
from typing import Union
import re

from pe.core import Scanner


class Dot(Scanner):
    def __init__(self):
        self._re = re.compile('.')


class Literal(Scanner):
    __slots__ = 'string',

    def __init__(self, string: str):
        self.string = string
        self._re = re.compile(re.escape(string))


class Class(Scanner):
    __slots__ = 'clsstr', 'negated',

    def __init__(self, clsstr: str, negate: bool = False):
        self.clsstr = clsstr
        self.negated = negate
        neg = '^' if negate else ''
        cls = clsstr.replace('[', '\\[').replace(']', '\\]')
        self._re = re.compile(f'[{neg}{cls}]')


Primitive = Union[str, Dot, Literal, Class]


def _validate(arg):
    if isinstance(arg, str):
        return Literal(arg)
    elif not isinstance(arg, Scanner):
        raise ValueError(f'not a valid Scanner: {arg!r}')
    else:
        return arg


class Run(Scanner):
    __slots__ = 'scanner', 'min', 'max',

    def __init__(self,
                 scanner: Scanner,
                 min: int = 0,
                 max: int = -1):
        self.scanner = _validate(scanner)
        self.min = min
        self.max = max
        inner = self.scanner._re.pattern
        re_max = '' if max < 0 else max
        self._re = re.compile(f'(?:{inner}){{{min},{re_max}}}')


def Option(scanner: Scanner):
    return Run(scanner, max=1)


class Until(Scanner):
    __slots__ = 'terminus', 'escape',

    def __init__(self,
                 terminus: Primitive,
                 escape: str = None):
        self.terminus = _validate(terminus)
        self.escape = escape

        if isinstance(self.terminus, Literal):
            cs = list(map(re.escape, self.terminus.string))
        elif isinstance(self.terminus, Class):
            if self.terminus.negated:
                raise ValueError('negated Class instances are not supported')
            cs = [self.terminus._re.pattern[1:-1]]
        else:
            raise TypeError('not a Literal or Class instance')

        alts = []
        if not escape:
            e = ''
        elif len(escape) > 1:
            raise ValueError(f'escape character is not length 1: {escape!r}')
        else:
            e = re.escape(escape)
            alts.append(f'{e}.[^{cs[0]}{e}]*')

        for i in range(1, len(cs)):
            alts.append(f'{cs[:i]}[^{cs[i:i+1]}]')
        etc = f'(?:{"|".join(alts)})*'

        self._re = re.compile(f'[^{cs[0]}{e}]*{etc}')


class Pattern(Scanner):
    __slots__ = 'scanners',

    def __init__(self, *scanners: Scanner):
        self.scanners = list(map(_validate, scanners))
        self._re = re.compile(''.join(s._re.pattern for s in self.scanners))


class Branch(Scanner):
    __slots__ = 'scanners',

    def __init__(self, *scanners: Scanner):
        self.scanners = list(map(_validate, scanners))
        self._re = re.compile(
            '(?:{})'.format('|'.join(s._re.pattern for s in self.scanners)))
