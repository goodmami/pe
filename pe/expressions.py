
from typing import Dict, Callable, Optional as OptionalType
import re

from pe.core import Match, Term, Expression
from pe.terms import Dot, Literal

# class Until(Term):
#     __slots__ = 'terminus', 'escape',

#     def __init__(self,
#                  terminus: Primitive,
#                  escape: str = None):
#         self.terminus = _validate(terminus)
#         self.escape = escape

#         if isinstance(self.terminus, Literal):
#             cs = list(map(re.escape, self.terminus.string))
#         elif isinstance(self.terminus, Class):
#             if self.terminus.negated:
#                 raise ValueError('negated Class instances are not supported')
#             cs = [self.terminus._re.pattern[1:-1]]
#         else:
#             raise TypeError('not a Literal or Class instance')

#         alts = []
#         if not escape:
#             e = ''
#         elif len(escape) > 1:
#             raise ValueError(f'escape character is not length 1: {escape!r}')
#         else:
#             e = re.escape(escape)
#             alts.append(f'{e}.[^{cs[0]}{e}]*')

#         for i in range(1, len(cs)):
#             alts.append(f'{cs[:i]}[^{cs[i:i+1]}]')
#         etc = f'(?:{"|".join(alts)})*'

#         self._re = re.compile(f'[^{cs[0]}{e}]*{etc}')


def _validate(arg):
    if isinstance(arg, str):
        return Literal(arg)
    elif not isinstance(arg, Expression):
        raise ValueError(f'not a valid Expression: {arg!r}')
    else:
        return arg


class Sequence(Expression):
    __slots__ = 'expressions',

    def __init__(self, *expressions):
        super().__init__()
        self.expressions = list(map(_validate, expressions))
        self.capturing = any(m.capturing for m in self.expressions)

        if all(e._re for e in self.expressions):
            self._re = re.compile(
                ''.join(e._re.pattern for e in self.expressions))

    def match(self, s: str, pos: int = 0):
        matches = []
        start = pos
        for expression in self.expressions:
            m = expression.match(s, pos=pos)
            if not m:
                return None
            pos = m.endpos
            matches.append(m)
        return Match(s, start, pos, self, matches)


class Choice(Expression):
    __slots__ = 'expressions',

    def __init__(self, *expressions):
        super().__init__()
        self.expressions = list(map(_validate, expressions))
        self.capturing = any(m.capturing for m in self.expressions)

        if all(e._re for e in self.expressions):
            self._re = re.compile(
                '(?:{})'.format(
                    '|'.join(e._re.pattern for e in self.expressions)))

    def match(self, s: str, pos: int = 0):
        m = None
        for expression in self.expressions:
            m = expression.match(s, pos=pos)
            if m:
                break
        return Match(s, pos, m.endpos, self, [m])


class Repeat(Expression):
    __slots__ = 'expression', 'min', 'max', 'delimiter',

    def __init__(self,
                 expression: Expression,
                 min: int = 0,
                 max: int = -1,
                 delimiter: Expression = None):
        super().__init__()
        if max >= 0 and max < min:
            raise Error('max must be -1 or >= min')
        self.expression: Expression = _validate(expression)
        self.min = min
        self.max = max
        if delimiter:
            delimiter = _validate(delimiter)
        self.delimiter: OptionalType[Expression] = delimiter
        self.capturing = (expression.capturing
                          or (delimiter and delimiter.capturing))

        _re = self.expression._re
        if max == 0:
            self._re = re.compile('')
        elif _re and (not delimiter or delimiter._re):
            delim = delimiter._re if delimiter else ''
            max2 = '' if max < 0 else max - 1
        self._re = re.compile(
            f'{_re.pattern}(?:{delim}{_re.pattern}){{{min},{max2}}}')


    def match(self, s: str, pos: int = 0):
        expression = self.expression
        delimiter = self.delimiter
        min = self.min
        max = self.max
        start: int = pos
        matches = []
        count: int = 0

        # TODO: walrus
        m = expression.match(s, pos=pos)
        while m is not None and count != max:
            pos = m.endpos
            matches.append(m)
            count += 1
            if delimiter:
                d = delimiter.match(s, pos=pos)
                if d:
                    break
                m = expression.match(s, pos=d.endpos)
                if m:
                    break
                matches.extend((d, m))
                pos = m.endpos
            else:
                m = expression.match(s, pos=pos)

        if count < min:
            return None
        return Match(s, start, pos, self, matches)


def Optional(expression: Expression):
    return Repeat(expression, max=1)


def Until(terminus: Expression, escape: Expression = None):
    run = Repeat(Sequence(NotAhead(terminus), Dot()))
    if escape:
        return Sequence(run, Repeat(Choice(escape, run)))
    else:
        return run


class Ahead(Expression):
    __slots__ = 'expression',

    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = _validate(expression)
        self._re = self.expression._re

    def match(self, s: str, pos: int = 0):
        m = self.expression.match(s, pos=pos)
        if m:
            return Match(s, pos, pos, self, [])
        return None


class NotAhead(Expression):
    __slots__ = 'expression',

    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = _validate(expression)
        # TODO: avoid use of lookahead?
        _re = self.expression._re
        if _re:
            self._re = re.compile(r'(?!{_re.pattern})')

    def match(self, s: str, pos: int = 0):
        m = self.expression.match(s, pos=pos)
        if m:
            return None
        return Match(s, pos, pos, self, [])


class Group(Expression):
    __slots__ = 'expression', 'action',

    def __init__(self, expression: Expression, action: Callable = None):
        super().__init__()
        self.expression = _validate(expression)
        self.action = action
        self.capturing = True
        self._re = self.expression._re

    def match(self, s: str, pos: int = 0):
        m = self.expression.match(s, pos=pos)
        if m:
            return Match(s, pos, m.endpos, self, [m])
        return None


class Nonterminal(Expression):
    __slots__ = 'name', 'rules',

    def __init__(self, name: str, rules: Dict[str, Expression]):
        super().__init__()
        self.name = name
        self.rules = rules

    def match(self, s: str, pos: int = 0):
        return self.rules[self.name].match(s, pos=pos)


class Grammar(Expression):
    __slots__ = 'rules', 'actions',

    def __init__(self, rules=None, actions=None):
        super().__init__()
        self.rules = {}
        self.actions = actions or {}
        if rules:
            for name, expression in rules.items():
                expression = _validate(expression)
                self.rules[name] = expression

    def __setitem__(self, name: str, expression: Expression):
        self.rules[name] = _validate(expression)

    def lookup(self, name: str) -> Expression:
        return Nonterminal(name, self.rules)

    def match(self, s: str, pos: int = 0):
        return self.rules['Start'].match(s, pos=pos)
