
"""
Packrat Parsing

"""

from typing import (
    Union, Tuple, Sequence, Dict, Callable, Pattern)
import re
from collections import defaultdict

from pe.constants import FAIL, Operator
from pe.core import Error, Match, Expression, Definition, Grammar

_MatchResult = Tuple[int, Sequence, Union[Dict, None]]
Memo = Dict[int, Dict[int, _MatchResult]]

#: Number of string positions that can be cached at one time.
MAX_MEMO_SIZE = 1000
_EMPTY_ARGS = ()
_FAIL_RESULT = (FAIL, _EMPTY_ARGS, None)


class _Expr(Expression):
    __slots__ = ()

    def match(self, s: str, pos: int = 0) -> Union[Match]:
        end, args, kwargs = self._match(s, pos, defaultdict(dict))
        if end < 0:
            return None
        args = tuple(args or ())
        if kwargs is None:
            kwargs = {}
        return Match(s, pos, end, self, args, kwargs)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        raise NotImplementedError()


# Terms (Dot, Literal, Class)

class Terminal(_Expr):
    """An atomic expression."""

    __slots__ = '_re',

    def __init__(self, pattern: str, flags: int = 0):
        self._re = re.compile(pattern, flags=flags)
        self.iterable = self._re.groups > 0

    def scan(self, s: str, pos: int = 0):
        # TODO: walrus
        m = self._re.match(s, pos)
        if not m:
            return FAIL
        return m.end()

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        m = self._re.match(s, pos)
        if not m:
            return _FAIL_RESULT
        args = m.groups() if self._re.groups else [m.group(0)]
        return m.end(), args, None


# Combining Expressions

class Sequence(_Expr):

    __slots__ = 'expressions',
    iterable = True

    def __init__(self, *expressions: _Expr):
        self.expressions = expressions

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
                return _FAIL_RESULT
            args.extend(_args)
            if _kwargs:
                kwargs.update(_kwargs)
            pos = end
        return pos, args, kwargs


class Choice(_Expr):

    __slots__ = 'expressions',
    iterable = True

    def __init__(self, *expressions: _Expr):
        self.expressions = expressions

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
        return _FAIL_RESULT


class Repeat(_Expr):

    __slots__ = 'expression', 'min', 'max',
    iterable = True

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
            ext(_args)
            if _kwargs:
                upd(_kwargs)
            pos = end
            count += 1

        if count < min:
            return _FAIL_RESULT
        return pos, args, kwargs


class Optional(_Expr):

    __slots__ = 'expression',
    iterable = True

    def __init__(self, expression: _Expr):
        self.expression = expression

    def scan(self, s: str, pos: int = 0):
        end = self.expression.scan(s, pos)
        if end >= 0:
            return end
        return pos

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if end < 0:
            return pos, _EMPTY_ARGS, None
        return end, args, kwargs


# Non-consuming Expressions

class Lookahead(_Expr):
    """An expression that may match but consumes no input."""

    __slots__ = 'expression', 'polarity',
    iterable = True

    def __init__(self, expression: _Expr, polarity: bool):
        self.expression = expression
        self.polarity = polarity

    def scan(self, s: str, pos: int = 0) -> int:
        matched = self.expression.scan(s, pos) >= 0
        if self.polarity ^ matched:
            return FAIL
        return pos

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        matched = self.expression._match(s, pos, memo)[0] >= 0
        if self.polarity ^ matched:
            return _FAIL_RESULT
        return pos, _EMPTY_ARGS, None


# Recursion and Rules

class Rule(_Expr):

    __slots__ = '_expression', '_action',

    def __init__(self,
                 expression: Union[_Expr, None],
                 action: Callable = None):
        self._expression = expression
        self._action = action
        self.finalize()

    @property
    def expression(self):
        return self._expression

    @expression.setter
    def expression(self, expression: _Expr):
        self._expression = expression
        self.finalize()

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, action: Union[Callable, None]):
        self._action = action
        self.finalize()

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
            expr = self.expression
            end, args, kwargs = expr._match(s, pos, memo)
            if end >= 0 and self.action:
                if isinstance(expr, (Bind, Lookahead)):
                    args = [self.action(**(kwargs or {}))]
                elif expr.iterable:
                    args = [self.action(args or (), **(kwargs or {}))]
                elif args:
                    args = [self.action(args[-1], **(kwargs or {}))]
                else:
                    args = [self.action(**(kwargs or {}))]
            memo[pos][_id] = (end, args, kwargs)
        return end, args, kwargs

    def finalize(self):
        if self._expression:
            self.iterable = self._action is None and self._expression.iterable


class Raw(_Expr):

    __slots__ = 'expression',
    iterable = False

    def __init__(self, expression: _Expr):
        self.expression = expression

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        return end, (s[pos:end],), None


class Bind(_Expr):

    __slots__ = 'expression', 'name',
    iterable = True

    def __init__(self, expression: _Expr, name: str = None):
        self.expression = expression
        self.name = name

    def scan(self, s: str, pos: int = 0):
        return self.expression.scan(s, pos=pos)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if end < 0:
            return _FAIL_RESULT
        name = self.name
        if name:
            if self.expression.iterable:
                bound = args
            elif args:
                bound = args[-1]
            else:
                bound = None
            if not kwargs:
                kwargs = {}
            kwargs[name] = bound
        return end, _EMPTY_ARGS, kwargs


class PackratParser(Expression):

    __slots__ = 'grammar', '_exprs',

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self._exprs: Dict[str, _Expr] = _grammar_to_packrat(grammar)

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

    def match(self, s: str, pos: int = 0) -> Match:
        return self._exprs[self.start].match(s, pos=pos)


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


def _def_to_expr(_def: Definition, defns, exprs):
    op, args = _def
    if op == Operator.DOT:
        return Terminal('.')
    elif op == Operator.LIT:
        return Terminal(re.escape(args[0]))
    elif op == Operator.CLS:
        return Terminal(f'[{args[0]}]')  # TODO: validate ranges
    elif op == Operator.RGX:
        return Terminal(args[0], flags=args[1])
    elif op == Operator.OPT:
        return Optional(_def_to_expr(args[0], defns, exprs))
    elif op == Operator.RPT:
        return Repeat(_def_to_expr(args[0], defns, exprs),
                      min=args[1], max=args[2])
    elif op == Operator.SYM:
        return exprs.setdefault(args[0], Rule(None))
    elif op == Operator.AND:
        return Lookahead(_def_to_expr(args[0], defns, exprs), True)
    elif op == Operator.NOT:
        return Lookahead(_def_to_expr(args[0], defns, exprs), False)
    elif op == Operator.RAW:
        return Raw(_def_to_expr(args[0], defns, exprs))
    elif op == Operator.BND:
        return Bind(_def_to_expr(args[1], defns, exprs), name=args[0])
    elif op == Operator.SEQ:
        return Sequence(*[_def_to_expr(e, defns, exprs) for e in args[0]])
    elif op == Operator.CHC:
        return Choice(*[_def_to_expr(e, defns, exprs) for e in args[0]])
    else:
        raise Error(f'invalid definition: {_def!r}')
