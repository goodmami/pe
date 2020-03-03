
"""
Packrat Parsing

"""

from typing import (
    Union, Tuple, Dict, Callable, Pattern)
import re
from collections import defaultdict

from pe.constants import FAIL, Operator
from pe.core import Error, Match, Expression, Grammar

_MatchResult = Tuple[int, Union[Tuple, None], Union[Dict, None]]
Memo = Dict[int, Dict[int, _MatchResult]]

#: Number of string positions that can be cached at one time.
MAX_MEMO_SIZE = 1000


class _Expr(Expression):
    __slots__ = ()

    def match(self, s: str, pos: int = 0) -> Union[Match]:
        end, args, kwargs = self._match(s, pos, defaultdict(dict))
        if end < 0:
            return None
        return Match(s, pos, end, self, args=args, kwargs=kwargs)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        raise NotImplementedError()


# Terms (Dot, Literal, Class)

class Regex(_Expr):
    """An atomic expression."""

    __slots__ = '_re',
    structured = False

    def __init__(self, pattern: str, flags: int = 0):
        self._re = re.compile(pattern, flags=flags)

    def scan(self, s: str, pos: int = 0):
        # TODO: walrus
        m = self._re.match(s, pos)
        if not m:
            return FAIL
        return m.end()

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        m = self._re.match(s, pos)
        if not m:
            return FAIL, None, None
        args = m.groups() if self._re.groups else None
        return m.end(), args, None


# Combining Expressions

class Sequence(_Expr):
    __slots__ = 'expressions',

    def __init__(self, *expressions: _Expr):
        self.expressions = expressions
        super().__init__(
            structured=any(e.structured for e in self.expressions))

    def scan(self, s: str, pos: int = 0):
        end = pos
        for e in self.expressions:
            end = e.scan(s, pos=end)
            if end < 0:
                break  # return fail code
        return end

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        args = []
        kwargs = {}
        for expression in self.expressions:
            end, _args, _kwargs = expression._match(s, pos, memo)
            if end < 0:
                return FAIL, None, None
            # since this is structured, resolve args now
            if _args is None:
                args.append(s[pos:end])
            else:
                args.extend(_args)
            if _kwargs:
                kwargs.update(_kwargs)
            pos = end
        return pos, args, kwargs


class Choice(_Expr):
    __slots__ = 'expressions',

    def __init__(self, *expressions: _Expr):
        self.expressions = expressions
        super().__init__(
            structured=any(m.structured for m in self.expressions))

    def scan(self, s: str, pos: int = 0):
        for e in self.expressions:
            end = e.scan(s, pos=pos)
            if end >= 0:
                return end
        return FAIL

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        for e in self.expressions:
            end, args, kwargs = e._match(s, pos, memo)
            if end >= 0:
                return end, args, kwargs
        return FAIL, None, None


class Repeat(_Expr):
    __slots__ = 'expression', 'min', 'max',

    def __init__(self,
                 expression: _Expr,
                 min: int = 0,
                 max: int = -1):
        if min < 0:
            raise ValueError('min must be >= 0')
        if max != -1 and max < min:
            raise ValueError('max must be -1 (unlimited) or >= min')
        self.expression = expression
        self.min = min
        self.max = max
        super().__init__(structured=self.expression.structured)

    def scan(self, s: str, pos: int = 0):
        min = self.min
        max = self.max
        guard = len(s) - pos  # simple guard against runaway left-recursion
        expr = self.expression
        count: int = 0
        while guard > 0 and count != max:
            end = expr.scan(s, pos)
            if end < 0:
                break
            pos = end
            count += 1
        if count < min:
            return FAIL
        return pos

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        expression = self.expression
        min = self.min
        max = self.max
        guard = len(s) - pos  # simple guard against runaway left-recursion

        args = []
        kwargs = {}
        ext = args.extend
        upd = kwargs.update()

        count: int = 0
        while guard > 0 and count != max:
            end, _args, _kwargs = expression._match(s, pos, memo)
            if end < 0:
                break
            pos = end
            count += 1
            if _args is not None:
                ext(_args)
            if _kwargs:
                upd(_kwargs)

        if count < min:
            return FAIL, None, None
        return pos, args, kwargs


# Non-consuming Expressions

class Lookahead(_Expr):
    """An expression that may match but consumes no input."""

    __slots__ = 'expression', 'polarity',

    def __init__(self, expression: _Expr, polarity: bool):
        self.expression = expression
        self.polarity = polarity
        super().__init__(structured=False)

    def scan(self, s: str, pos: int = 0) -> int:
        matched = self.expression.scan(s, pos) >= 0
        if self.polarity ^ matched:
            return FAIL
        return pos

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        matched = self.expression._match(s, pos, memo)[0] >= 0
        if self.polariy ^ matched:
            return FAIL
        return pos, None, None


# Recursion and Rules

class Rule(_Expr):
    __slots__ = 'expression', 'action',

    def __init__(self,
                 expression: Union[_Expr, None],
                 action: Callable = None):
        self.expression = expression
        self.action = action
        super().__init__(
            structured=(expression is None
                        or expression.structured
                        or action is not None))

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        _id = id(self)
        if pos in memo and _id in memo[pos]:
            end, args, kwargs = memo[pos][_id]  # packrat memoization check
        else:
            # clear memo beyond size limit
            while len(memo) > MAX_MEMO_SIZE:
                del memo[min(memo)]
            end, args, kwargs = self.expression._match(s, pos, memo)
            if end >= 0 and self.action:
                # resolve value if necessary
                if args is None:
                    args = [s[pos:end]]
                args = [self.action(*(args or ()), **(kwargs or {}))]
            memo[pos][_id] = (end, args, kwargs)
        return end, args, kwargs


class Bind(_Expr):
    __slots__ = 'expression', 'name',
    structured = True

    def __init__(self, expression: _Expr, name: str = None):
        self.expression = expression
        self.name = name

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if end < 0:
            return end, None, None
        name = self.name
        if name:
            bound = s[pos:end] if args is None else args
            if not kwargs:
                kwargs = {}
            kwargs[name] = bound
        return end, [], kwargs


class PackratParser(Expression):
    __slots__ = 'grammar', '_exprs',

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self._exprs: Dict[str, _Expr] = _grammar_to_packrat(grammar)
        super().__init__(structured=True)

    @property
    def start(self):
        return self.grammar.start

    def __getitem__(self, name: str) -> Expression:
        return self._exprs[name]

    def __contains__(self, name: str) -> bool:
        return name in self._exprs

    def scan(self, s: str, pos: int = 0):
        if self.start not in self:
            raise Error(f'start rule not defined')
        return self[self.start].scan(s, pos=pos)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        return self.rules[self.start]._match(s, pos, memo)


def _grammar_to_packrat(grammar):
    defns = grammar.definitions
    actns = grammar.actions
    exprs = {}
    for name, _def in defns.items():
        if name not in exprs:
            expr = _def_to_expr(_def, defns, exprs)
            if name in actns:
                expr = Rule(expr, action=actns[name])
            exprs[name] = expr
        else:
            expr = exprs[name]
            if isinstance(expr, Rule) and expr.expression is None:
                expr.expression = _def_to_expr(_def, defns, exprs)
            expr.action = actns.get(name)
    return exprs


def _def_to_expr(_def, defns, exprs):
    op = _def[0]
    if op == Operator.DOT:
        return Regex('.')
    elif op == Operator.LIT:
        return Regex(re.escape(_def[1]))
    elif op == Operator.CLS:
        return Regex(f'[{_def[1]}]')  # TODO: validate ranges
    elif op == Operator.RGX:
        return Regex(term[1], flags=term[2])
    elif op == Operator.SEQ:
        return Sequence(*[_def_to_expr(e, defns, exprs) for e in _def[1]])
    elif op == Operator.CHC:
        return Choice(*[_def_to_expr(e, defns, exprs) for e in _def[1]])
    elif op == Operator.RPT:
        return Repeat(_def_to_expr(_def[1], defns, exprs),
                      min=_def[2], max=_def[3])
    elif op == Operator.SYM:
        return exprs.setdefault(_def[1], Rule(None))
    elif op == Operator.AND:
        return Lookahead(_def_to_expr(_def[1], defns, exprs), True)
    elif op == Operator.NOT:
        return Lookahead(_def_to_expr(_def[1], defns, exprs), False)
    elif op == Operator.BND:
        return Bind(_def_to_expr(_def[2], defns, exprs), name=_def[1])
    else:
        raise Error(f'invalid definition: {_def!r}')
