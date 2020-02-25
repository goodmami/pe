
from typing import Union, Dict, Callable, Optional as OptionalType
import re

from pe.constants import NOMATCH
from pe.core import (
    Match,
    Expression,
    Lookahead,
    Error,
)
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
    __slots__ = 'expressions', '_val_modes'

    def __init__(self, *expressions: _NiceExpr):
        self.expressions = list(map(_validate, expressions))
        super().__init__(
            structured=any(e.structured for e in self.expressions),
            filtered=any(e.filtered for e in self.expressions))

    def __str__(self):
        return 'Sequence({})'.format(', '.join(map(str, self.expressions)))

    def scan(self, s: str, pos: int = 0):
        if self._re:
            m = self._re.match(s, pos)
            end = NOMATCH if not m else m.end()
        else:
            end = pos
            for e in self.expressions:
                end = e.scan(s, pos=end)
                if end < 0:
                    break
        return end

    def _match(self, s: str, pos: int = 0):
        if not self.structured and self._re:
            m = self._re.match(s, pos)
            if not m:
                return NOMATCH, None
            return m.end(), m.group()

        unfiltered = not self.filtered
        value = []
        start = pos
        for expression in self.expressions:
            end, _value = expression._match(s, pos=pos)
            if end < 0:
                return NOMATCH, None
            pos = end
            if unfiltered:
                value.append(_value)
            elif expression.filtered:
                value.extend(_value)
        if not self.structured:
            value = ''.join(value)
        return pos, value


class Choice(Expression):
    __slots__ = 'expressions',

    def __init__(self, *expressions: _NiceExpr):
        self.expressions = list(map(_validate, expressions))
        super().__init__(
            structured=any(m.structured for m in self.expressions),
            filtered=any(m.filtered for m in self.expressions))

    def __str__(self):
        return 'Choice({})'.format(', '.join(map(str, self.expressions)))

    def scan(self, s: str, pos: int = 0):
        if self._re:
            m = self._re.match(s, pos)
            end = NOMATCH if not m else m.end()
        else:
            end = NOMATCH
            for e in self.expressions:
                end = e.scan(s, pos=pos)
                if end >= 0:
                    break
        return end

    def _match(self, s: str, pos: int = 0):
        if not self.structured and self._re:
            m = self._re.match(s, pos)
            if not m:
                return NOMATCH, None
            return m.end(), [m.group()]

        struct = self.structured
        end = NOMATCH
        for expression in self.expressions:
            end, groups = expression._match(s, pos=pos)
            if end >= 0:
                if struct and not expression.structured:
                    groups = []
                return end, groups
        return end, None


def _scan_with_escape(s, pos, expr, esc):
    if esc:
        end = esc.scan(s, pos)
        if end >= pos:
            pos = end
    pos = expr.scan(s, pos)
    if pos >= 0 and esc:
        end = esc.scan(s, pos)
        if end >= pos:
            pos = end
    return pos


def _match_escape(s, pos, escape, accumulate):
    # TODO: not correct; consider a{:(?:" "? (delim))*}
    end, _value = escape._match(s, pos=pos)
    while end > pos:
        pos = end
        if accumulate:
            accumulate(_value)
        end, _value = escape._match(s, pos=pos)
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
            structured=(self.expression.structured
                        or (delimiter and delimiter.structured)
                        or (escape and escape.structured)),
            filtered=(self.expression.filtered
                      or (delimiter and delimiter.filtered)
                      or (escape and escape.filtered)))

    def __str__(self):
        return (f'Repeat({self.expression!s}, '
                f'min={self.min}, max={self.max}, '
                f'delimiter={self.delimiter!s}, '
                f'escape={self.escape!s})')

    def scan(self, s: str, pos: int = 0):
        if self._re:
            m = self._re.match(s, pos)
            return NOMATCH if not m else m.end()
        else:
            min = self.min
            max = self.max
            expr = self.expression
            delim = self.delimiter
            esc = self.escape
            if max == 0:
                if esc:
                    end = esc.scan(s, pos)
                    if end >= pos:
                        pos = end
                return pos
            else:
                pos = _scan_with_escape(s, pos, expr, esc)
                count = 1
                while pos >= 0 and count != max:
                    if delim:
                        end = delim.scan(s, pos=pos)
                        if end < 0:
                            break
                        end = _scan_with_escape(s, end, expr, esc)
                    else:
                        end = _scan_with_escape(s, end, expr, esc)
                    if end < 0:
                        break
                    pos = end
                    count += 1
            if count < min:
                return NOMATCH
            return pos

    def _match(self, s: str, pos: int = 0):
        if not self.structured and self._re:
            m = self._re.match(s, pos)
            if not m:
                return NOMATCH, None
            return m.end(), [m.group()]

        expression = self.expression
        delimiter = self.delimiter
        escape = self.escape
        min = self.min
        max = self.max
        start: int = pos

        value = []
        if self.filtered:
            acc = value.extend if expression.filtered else None
            dacc = value.extend if delimiter and delimiter.filtered else None
            eacc = value.extend if escape and escape.filtered else None
        else:
            acc = dacc = eacc = value.append

        if escape:
            pos = _match_escape(s, pos, escape, eacc)

        count: int = 0
        end: int = NOMATCH
        # first instance, pre-delimiter
        if max != 0:
            end, _value = expression._match(s, pos=pos)
            if end >= pos and acc:
                acc(_value)
                pos = end
                count += 1

        # TODO: walrus
        while count != max:
            if escape:
                pos = _match_escape(s, pos, escape, eacc)
            if delimiter:
                end, dvalue = delimiter._match(s, pos=pos)
                if end < 0:
                    break
                if escape:
                    end = _match_escape(s, end, escape, eacc)
                end, _value = expression._match(s, pos=end)
                if end >= pos and dacc:
                    dacc(dvalue)
            else:
                end, _value = expression._match(s, pos=pos)

            if end < 0:
                break
            if acc:
                acc(_value)
            pos = end

        if escape:
            pos = _match_escape(s, pos, escape, eacc)

        if count < min:
            return NOMATCH, None
        return pos, value


def Optional(expression: _NiceExpr):
    return Repeat(expression, max=1)


def Peek(expression):
    return Lookahead(_validate(expression), True)


def Not(expression):
    return Lookahead(_validate(expression), False)


class Group(Expression):
    __slots__ = 'expression', 'action',

    def __init__(self, expression: _NiceExpr):
        self.expression = _validate(expression)
        super().__init__(structured=True, filtered=True)

    def __str__(self):
        return f'Group({self.expression!s})'

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int = 0):
        end, value = self.expression._match(s, pos=pos)
        if end < 0:
            return end, None
        return end, [value]


class _DeferredLookup(Expression):
    def __init__(self, name: str, table: Dict[str, OptionalType[Expression]]):
        self.name = name
        self.table = table
        self.structured = True  # until it is knowable
        self.filtered = False  # until it is knowable
        self._re = None

    def __str__(self):
        return f'_DeferredLookup({self.name})'

    def scan(self, s: str, pos: int = 0):
        expr = self.table[self.name]
        if expr is None:
            raise Error(f'expression not defined: {self.name}')
        return expr.scan(s, pos=pos)

    def _match(self, s: str, pos: int = 0):
        expr = self.table[self.name]
        if expr is None:
            raise Error(f'expression not defined: {self.name}')
        return expr._match(s, pos=pos)


class Rule(Expression):
    __slots__ = 'expression', 'name', 'action',

    def __init__(self,
                 expression: Expression,
                 name: str = None,
                 action: Callable = None):
        self.expression = _validate(expression)
        self.name = name
        self.action = action
        super().__init__(structured=action is not None,
                         filtered=self.expression.filtered)

    def __str__(self):
        return (f'Rule({self.expression!s}, '
                f'name={self.name!r}, '
                f'action={self.action})')

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int = 0):
        end, value = self.expression._match(s, pos=pos)
        if end < 0:
            return end, None
        if self.action:
            value = self.action(value)
        return end, value


class Grammar(Expression):
    __slots__ = 'rules', 'actions', 'start',

    def __init__(self, rules=None, actions=None, start='Start'):
        self.rules = rules or {}
        self.actions = actions or {}
        self.start = start
        if rules:
            for name, expression in rules.items():
                expression = _validate(expression)
                self.rules[name] = expression
        super().__init__(structured=True)

    def __setitem__(self, name: str, expression: Expression):
        self.rules[name] = _validate(expression)

    def __getitem__(self, name: str) -> Expression:
        # TODO: walrus
        expr = self.rules.get(name)
        if expr:
            return expr
        else:
            return _DeferredLookup(name, self.rules)

    def __contains__(self, name: str) -> bool:
        return name in self.rules

    def scan(self, s: str, pos: int = 0):
        if self.start not in self:
            raise Error(f'start rule not defined')
        return self[self.start].scan(s, pos=pos)

    def _match(self, s: str, pos: int = 0):
        return self.rules[self.start]._match(s, pos=pos)
