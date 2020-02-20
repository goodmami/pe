
from typing import Union, Dict, Callable, Optional as OptionalType
import re

from pe.core import Match, Term, Expression
from pe.terms import Dot, Literal, Class


_NiceExpr = Union[str, Expression]


def _validate(arg):
    if isinstance(arg, str):
        return Literal(arg)
    elif not isinstance(arg, Expression):
        raise ValueError(f'not a valid Expression: {arg!r}')
    else:
        return arg


class Sequence(Expression):
    __slots__ = 'expressions',

    def __init__(self, *expressions: _NiceExpr):
        self.expressions = list(map(_validate, expressions))
        super().__init__(capturing=any(m.capturing for m in self.expressions))

    def __str__(self):
        return 'Sequence({})'.format(', '.join(map(str, self.expressions)))

    def match(self, s: str, pos: int = 0):
        if not self.capturing and self._re:
            m = self._re.match(s, pos)
            if not m:
                return None
            return Match(s, pos, m.end(), self, [])

        matches = []
        start = pos
        for expression in self.expressions:
            m = expression.match(s, pos=pos)
            if not m:
                return None
            pos = m.end
            matches.append(m)
        return Match(s, start, pos, self, matches)


class Choice(Expression):
    __slots__ = 'expressions',

    def __init__(self, *expressions: _NiceExpr):
        self.expressions = list(map(_validate, expressions))
        super().__init__(capturing=any(m.capturing for m in self.expressions))

    def __str__(self):
        return 'Choice({})'.format(', '.join(map(str, self.expressions)))

    def match(self, s: str, pos: int = 0):
        if not self.capturing and self._re:
            m = self._re.match(s, pos)
            if not m:
                return None
            return Match(s, pos, m.end(), self, [])

        m = None
        for expression in self.expressions:
            print(expression, s, pos)
            print(expression._re)
            m = expression.match(s, pos=pos)
            print(m)
            if m:
                return Match(s, pos, m.end, self, [m])
        return None


def _match_escape(s, pos, escape, matches):
    x = escape.match(s, pos=pos)
    while x is not None and pos != x.end:
        pos = x.end
        matches.append(x)
        x = escape.match(s, pos=pos)
    return pos


class Repeat(Expression):
    __slots__ = 'expression', 'min', 'max', 'delimiter', 'escape',

    def __init__(self,
                 expression: _NiceExpr,
                 min: int = 0,
                 max: int = -1,
                 delimiter: _NiceExpr = None,
                 escape: _NiceExpr = None):
        if min < 0:
            raise ValueError('min must be >= 0')
        if max != -1 and max < min:
            raise ValueError('max must be -1 (unlimited) or >= min')
        self.expression: Expression = _validate(expression)
        self.min = min
        self.max = max
        if delimiter:
            delimiter = _validate(delimiter)
        self.delimiter: OptionalType[Expression] = delimiter
        if escape:
            escape = _validate(escape)
        self.escape: OptionalType[Expression] = escape
        super().__init__(
            capturing=(self.expression.capturing
                       or (delimiter and delimiter.capturing)
                       or (escape and escape.capturing)))

    def __str__(self):
        return (f'Repeat({self.expression!s}, '
                f'min={self.min}, max={self.max}, '
                f'delimiter={self.delimiter!s}, '
                f'escape={self.escape!s})')

    def match(self, s: str, pos: int = 0):
        if not self.capturing and self._re:
            m = self._re.match(s, pos)
            if not m:
                return None
            return Match(s, pos, m.end(), self, [])

        expression = self.expression
        delimiter = self.delimiter
        escape = self.escape
        min = self.min
        max = self.max
        start: int = pos
        matches = []
        count: int = 0

        if escape:
            pos = _match_escape(s, pos, escape, matches)

        # TODO: walrus
        m = expression.match(s, pos=pos)
        while m is not None and count != max and pos != m.end:
            pos = m.end
            matches.append(m)
            count += 1

            if escape:
                pos = _match_escape(s, pos, escape, matches)

            if delimiter:
                d = delimiter.match(s, pos=pos)
                if not d:
                    break

                if escape:
                    pos = _match_escape(s, pos, escape, matches)

                m = expression.match(s, pos=d.end)
                if not m:
                    break
                matches.extend((d, m))
                pos = m.end
            else:
                m = expression.match(s, pos=pos)

        if escape:
            pos = _match_escape(s, pos, escape, matches)

        if count < min:
            return None
        return Match(s, start, pos, self, matches)


def Optional(expression: _NiceExpr):
    return Repeat(expression, max=1)


class Ahead(Expression):
    __slots__ = 'expression',

    def __init__(self, expression: _NiceExpr):
        self.expression = _validate(expression)
        super().__init__(caputuring=False)

    def __str__(self):
        return f'Ahead({self.expression!s})'

    def match(self, s: str, pos: int = 0):
        if self._re:
            m = self._re.match(s, pos)
            if not m:
                return None
            return Match(s, pos, pos, self, [])

        m = self.expression.match(s, pos=pos)
        if m:
            return Match(s, pos, pos, self, [])
        return None


class NotAhead(Expression):
    __slots__ = 'expression',

    def __init__(self, expression: _NiceExpr):
        self.expression = _validate(expression)
        super().__init__(capturing=False)

    def __str__(self):
        return f'NotAhead({self.expression!s})'

    def match(self, s: str, pos: int = 0):
        if self._re:
            m = self._re.match(s, pos)
            if not m:
                return None
            return Match(s, pos, pos, self, [])

        m = self.expression.match(s, pos=pos)
        if m:
            return None
        return Match(s, pos, pos, self, [])


class Group(Expression):
    __slots__ = 'expression', 'action',

    def __init__(self, expression: _NiceExpr, action: Callable = None):
        self.expression = _validate(expression)
        self.action = action
        super().__init__(capturing=True)

    def __str__(self):
        return f'Group({self.expression!s}, action={self.action!s})'

    def match(self, s: str, pos: int = 0):
        m = self.expression.match(s, pos=pos)
        if m:
            return Match(s, pos, m.end, self, [m])
        return None


class Nonterminal(Expression):
    __slots__ = 'name', 'rules',

    def __init__(self, name: str, rules: Dict[str, Expression]):
        self.name = name
        self.rules = rules
        super().__init__(capturing=False)

    def __str__(self):
        return f'Nonterminal({self.name}, rules=...)'

    def match(self, s: str, pos: int = 0):
        return self.rules[self.name].match(s, pos=pos)


class Grammar(Expression):
    __slots__ = 'rules', 'actions',

    def __init__(self, rules=None, actions=None):
        self.rules = {}
        self.actions = actions or {}
        if rules:
            for name, expression in rules.items():
                expression = _validate(expression)
                self.rules[name] = expression
        super().__init__(capturing=False)

    def __setitem__(self, name: str, expression: Expression):
        self.rules[name] = _validate(expression)

    def lookup(self, name: str) -> Expression:
        return Nonterminal(name, self.rules)

    def match(self, s: str, pos: int = 0):
        return self.rules['Start'].match(s, pos=pos)
