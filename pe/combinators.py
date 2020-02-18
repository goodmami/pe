
from typing import Dict, Callable

from pe.core import Match, Matcher, Combinator
from pe.scanners import Literal


def _validate(arg):
    if isinstance(arg, str):
        return Literal(arg)
    elif not isinstance(arg, Matcher):
        raise ValueError(f'not a valid Matcher: {arg!r}')
    else:
        return arg


class Sequence(Combinator):
    __slots__ = 'matchers',

    def __init__(self, *matchers):
        self.matchers = list(map(_validate, matchers))
        self.capturing = any(m.capturing for m in self.matchers)

    def match(self, s: str, pos: int = 0):
        matches = []
        start = pos
        for matcher in self.matchers:
            m = matcher.match(s, pos=pos)
            if not m:
                return None
            pos = m.endpos
            matches.append(m)
        return Match(s, start, pos, self, matches)


class Choice(Combinator):
    __slots__ = 'matchers',

    def __init__(self, *matchers):
        self.matchers = list(map(_validate, matchers))
        self.capturing = any(m.capturing for m in self.matchers)

    def match(self, s: str, pos: int = 0):
        m = None
        for matcher in self.matchers:
            m = matcher.match(s, pos=pos)
            if m:
                break
        return Match(s, pos, m.endpos, self, [m])


class Repeat(Combinator):
    __slots__ = 'matcher', 'min', 'max', 'delimiter',

    def __init__(self,
                 matcher: Matcher,
                 min: int = 0,
                 max: int = -1,
                 delimiter: Matcher = None):
        self.matcher: Matcher = _validate(matcher)
        self.min = min
        self.max = max
        if delimiter:
            delimiter = _validate(delimiter)
        self.delimiter: Matcher = delimiter
        self.capturing = (matcher.capturing
                          or (delimiter and delimiter.capturing))

    def match(self, s: str, pos: int = 0):
        matcher = self.matcher
        delimiter = self.delimiter
        min = self.min
        max = self.max
        start: int = pos
        matches = []
        count: int = 0

        # TODO: walrus
        m = matcher.match(s, pos=pos)
        while m is not None and count != max:
            pos = m.endpos
            matches.append(m)
            count += 1
            if delimiter:
                d = delimiter.match(s, pos=pos)
                if d:
                    break
                m = matcher.match(s, pos=d.endpos)
                if m:
                    break
                matches.extend((d, m))
                pos = m.endpos
            else:
                m = matcher.match(s, pos=pos)

        if count < min:
            return None
        return Match(s, start, pos, self, matches)


class Group(Combinator):
    __slots__ = 'matcher', 'action',

    def __init__(self, matcher: Matcher, action: Callable = None):
        self.matcher = _validate(matcher)
        self.action = action
        self.capturing = True

    def match(self, s: str, pos: int = 0):
        m = self.matcher.match(s, pos=pos)
        if m:
            return Match(s, pos, m.endpos, self, [m])
        return None


class Nonterminal(Combinator):
    __slots__ = 'name', 'rules',

    def __init__(self, name: str, rules: Dict[str, Matcher]):
        self.name = name
        self.rules = rules
        self.capturing = False

    def match(self, s: str, pos: int = 0):
        return self.rules[self.name].match(s, pos=pos)


class Grammar(Combinator):
    __slots__ = 'rules', 'actions',

    def __init__(self, rules=None, actions=None):
        self.rules = {}
        self.actions = actions or {}
        if rules:
            for name, matcher in rules.items():
                matcher = _validate(matcher)
                self.rules[name] = matcher

    def __setitem__(self, name: str, matcher: Matcher):
        self.rules[name] = _validate(matcher)

    def lookup(self, name: str) -> Matcher:
        return Nonterminal(name, self.rules)

    def match(self, s: str, pos: int = 0):
        return self.rules['Start'].match(s, pos=pos)
