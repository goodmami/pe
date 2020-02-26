
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
    __slots__ = 'expressions',

    def __init__(self, *expressions: _NiceExpr):
        self.expressions = list(map(_validate, expressions))
        super().__init__(
            structured=any(e.structured for e in self.expressions),
            filtered=any(e.filtered for e in self.expressions))

    def __repr__(self):
        return 'Sequence({})'.format(', '.join(map(repr, self.expressions)))

    def __str__(self):
        es = []
        for e in self.expressions:
            if isinstance(e, (Choice, Sequence)):
                es.append(f'(?:{e!s})')
            else:
                es.append(str(e))
        return ' '.join(es)

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

    def _match(self, s: str, pos: int):
        if not self.structured and self._re:
            m = self._re.match(s, pos)
            if not m:
                return NOMATCH, None
            return m.end(), m.group()

        unfiltered = not self.filtered
        value = []
        for expression in self.expressions:
            end, _value = expression._match(s, pos)
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

    def __repr__(self):
        return 'Choice({})'.format(', '.join(map(repr, self.expressions)))

    def __str__(self):
        return ' / '.join(map(str, self.expressions))

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

    def _match(self, s: str, pos: int):
        if not self.structured and self._re:
            m = self._re.match(s, pos)
            if not m:
                return NOMATCH, None
            return m.end(), [m.group()]

        struct = self.structured
        end = NOMATCH
        for expression in self.expressions:
            end, groups = expression._match(s, pos)
            if end >= 0:
                if struct and not expression.structured:
                    groups = []
                return end, groups
        return end, None


class Repeat(Expression):
    __slots__ = 'expression', 'min', 'max', 'delimiter',

    def __init__(self,
                 expression: _NiceExpr,
                 min: int = 0,
                 max: int = -1,
                 delimiter: _NiceExpr = None):
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
        super().__init__(
            structured=(self.expression.structured
                        or (delimiter and delimiter.structured)),
            filtered=(self.expression.filtered
                      or (delimiter and delimiter.filtered)))

    def __repr__(self):
        return (f'Repeat({self.expression!s}, '
                f'min={self.min}, max={self.max}, '
                f'delimiter={self.delimiter!s})')

    def __str__(self):
        qs = {(0, 1): '?', (0, -1): '*', (1, -1): '+'}
        e = str(self.expression)
        if isinstance(self.expression, (Sequence, Choice, Peek, Not)):
            e = f'(?:{e})'
        if self.delimiter or (self.min, self.max) not in qs:
            min = '' if self.min == 0 else self.min
            max = '' if self.max == -1 else self.max
            delim = f':{self.delimiter!s}' if self.delimiter else ''
            if min == '' and max == '' and delim:
                return f'{e}{{{delim}}}'
            else:
                return f'{e}{{{min},{max}{delim}}}'
        else:
            q = qs[(self.min, self.max)]
            return f'{e}{q}'

    def scan(self, s: str, pos: int = 0):
        max = self.max
        if self._re:
            m = self._re.match(s, pos)
            pos = NOMATCH if not m else m.end()
        elif max != 0:
            min = self.min
            expr = self.expression
            delim = self.delimiter
            end = expr.scan(s, pos)
            count: int = 0
            if end >= 0:
                pos = end
                count += 1
                while count != max:
                    if delim:
                        end = delim.scan(s, pos=pos)
                        if end >= 0:
                            end = expr.scan(s, end)
                    else:
                        end = expr.scan(s, pos)
                    if end < 0:
                        break
                    pos = end
                    count += 1
            if count < min:
                return NOMATCH
        return pos

    def _match(self, s: str, pos: int):
        if not self.structured and self._re:
            m = self._re.match(s, pos)
            if not m:
                return NOMATCH, None
            return m.end(), [m.group()]
        elif self.max == 0:
            return pos

        expression = self.expression
        delimiter = self.delimiter
        min = self.min
        max = self.max

        value = []
        if self.filtered:
            acc = value.extend if expression.filtered else None
            dacc = value.extend if delimiter and delimiter.filtered else None
        else:
            acc = dacc = value.append

        count: int = 0
        end, _value = expression._match(s, pos)
        if end >= pos:
            pos = end
            count += 1
            if acc:
                acc(_value)

            # TODO: walrus
            while count != max:
                if delimiter:
                    end, dvalue = delimiter._match(s, pos)
                    if end >= 0:
                        end, _value = expression._match(s, end)
                        if end >= 0 and dacc:
                            dacc(dvalue)
                else:
                    end, _value = expression._match(s, pos)

                if end < 0:
                    break
                if acc:
                    acc(_value)
                pos = end
                count += 1

        if count < min:
            return NOMATCH, None
        return pos, value


def Optional(expression: _NiceExpr):
    return Repeat(expression, max=1)


class Peek(Lookahead):
    def __init__(self, expression: Expression):
        super().__init__(expression, True)

    def __str__(self):
        e = str(self.expression)
        if isinstance(self.expression, (Sequence, Choice, Repeat)):
            e = f'(?:{e})'
        return f'&{e}'


class Not(Lookahead):
    def __init__(self, expression: Expression):
        super().__init__(expression, False)

    def __str__(self):
        e = str(self.expression)
        if isinstance(self.expression, (Sequence, Choice, Repeat)):
            e = f'(?:{e})'
        return f'!{e}'


class Group(Expression):
    __slots__ = 'expression', 'action',

    def __init__(self, expression: _NiceExpr):
        self.expression = _validate(expression)
        super().__init__(structured=True, filtered=True)

    def __repr__(self):
        return f'Group({self.expression!s})'

    def __str__(self):
        return f'({self.expression!s})'

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int):
        end, value = self.expression._match(s, pos)
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

    def __repr__(self):
        return f'_DeferredLookup({self.name})'

    def scan(self, s: str, pos: int = 0):
        expr = self.table[self.name]
        if expr is None:
            raise Error(f'expression not defined: {self.name}')
        return expr.scan(s, pos=pos)

    def _match(self, s: str, pos: int):
        expr = self.table[self.name]
        if expr is None:
            raise Error(f'expression not defined: {self.name}')
        return expr._match(s, pos)


class Rule(Expression):
    __slots__ = 'expression', 'action',

    def __init__(self,
                 expression: Expression,
                 action: Callable = None):
        self.expression = _validate(expression)
        self.action = action
        super().__init__(structured=action is not None,
                         filtered=self.expression.filtered)

    def __repr__(self):
        return (f'Rule({self.expression!s}, '
                f'action={self.action})')

    def __str__(self):
        return f'{self.expression!s}'

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int):
        end, value = self.expression._match(s, pos)
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

    def __str__(self):
        width = max(len(name) for name in self.rules) + 1
        defs = [f'{name:<{width}}<- {expr!s}'
                for name, expr in self.rules.items()]
        return '\n'.join(defs)

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

    def _match(self, s: str, pos: int):
        return self.rules[self.start]._match(s, pos)
