
from typing import Tuple, Dict, Optional

from pe._errors import ParseError
from pe._match import determine


class Action:
    def __repr__(self):
        return f'{type(self).__name__}({self.arg!r})'

    def __call__(self,
                 s: str,
                 pos: int,
                 end: int,
                 args: Tuple,
                 kwargs: Optional[Dict]) -> Tuple[Tuple, Optional[Dict]]:
        raise NotImplementedError


class Call(Action):
    def __init__(self, func):
        self.arg = func

    def __call__(self, s, pos, end, args, kwargs):
        return (self.arg(*args, **kwargs),), None


class Raw(Action):
    def __init__(self, func=str):
        self.arg = func

    def __call__(self, s, pos, end, args, kwargs):
        return (self.arg(s[pos:end]),), None


class Bind(Action):
    def __init__(self, name: str):
        self.arg = name

    def __call__(self, s, pos, end, args, kwargs):
        kwargs = dict(kwargs or [])
        kwargs[self.arg] = determine(args)
        return (), kwargs


class Constant(Action):

    def __init__(self, value):
        self.arg = value

    def __call__(self, s, pos, end, args, kwargs):
        return (self.arg,), None


class Pack(Action):

    def __init__(self, func):
        self.arg = func

    def __call__(self, s, pos, end, args, kwargs):
        return (self.arg(args, **kwargs),), None


class Join(Action):

    def __init__(self, func, sep=''):
        self.arg = func
        self.sep = sep

    def __repr__(self):
        return f'{type(self).__name__}({self.arg!r}, {self.sep!r})'

    def __call__(self, s, pos, end, args, kwargs):
        return (self.arg(self.sep.join(args), **kwargs),), None


class Getter(Action):
    def __init__(self, i):
        self.arg = i

    def __call__(self, s, pos, end, args, kwargs):
        return (args[self.arg],), None


class Fail(Action):

    def __init__(self, message):
        self.arg = message

    def __call__(self, s, pos, end, args, kwargs):
        raise ParseError.from_pos(
            pos, s, message=self.arg.format(*args, **kwargs))
