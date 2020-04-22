
from typing import Tuple, Dict, Optional

from pe._errors import ParseError
from pe._match import determine


class Action:
    def __call__(self,
                 s: str,
                 pos: int,
                 end: int,
                 args: Tuple,
                 kwargs: Optional[Dict]) -> Tuple[Tuple, Optional[Dict]]:
        raise NotImplementedError


class Call(Action):
    def __init__(self, func):
        self.func = func

    def __call__(self, s, pos, end, args, kwargs):
        return (self.func(*args, **kwargs),), None


class Raw(Action):
    def __init__(self, func=str):
        self.func = func

    def __call__(self, s, pos, end, args, kwargs):
        return (self.func(s[pos:end]),), None


class Bind(Action):
    def __init__(self, name: str):
        self.name = name

    def __call__(self, s, pos, end, args, kwargs):
        kwargs = dict(kwargs or [])
        kwargs[self.name] = determine(args)
        return (), kwargs


class Constant(Action):

    def __init__(self, value):
        self.value = value

    def __call__(self, s, pos, end, args, kwargs):
        return (self.value,), None


class Pack(Action):

    def __init__(self, func):
        self.func = func

    def __call__(self, s, pos, end, args, kwargs):
        return (self.func(args, **kwargs),), None


class Join(Action):

    def __init__(self, func, sep=''):
        self.func = func
        self.sep = sep

    def __call__(self, s, pos, end, args, kwargs):
        return (self.func(self.sep.join(args), **kwargs),), None


class Getter(Action):
    def __init__(self, i):
        self.i = i

    def __call__(self, s, pos, end, args, kwargs):
        return (args[self.i],), None


class Fail(Action):

    def __init__(self, message):
        self.message = message

    def __call__(self, s, pos, end, args, kwargs):
        raise ParseError.from_pos(
            pos, s, message=self.message.format(*args, **kwargs))
