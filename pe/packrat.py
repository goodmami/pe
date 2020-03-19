
"""
Packrat Parsing

"""

from typing import (
    Union, Tuple, Sequence as SeqType, Set, Dict, Callable, Pattern)
import re
from collections import defaultdict

from pe._constants import FAIL, Operator, Value, Flag
from pe._core import (
    Error,
    ParseError,
    Match,
    Expression,
    evaluate,
    Definition,
    Grammar,
)


_MatchResult = Tuple[int, SeqType, Union[Dict, None]]
Memo = Dict[int, Dict[int, _MatchResult]]

#: Number of string positions that can be cached at one time.
MAX_MEMO_SIZE = 1000
DEL_MEMO_SIZE = 500



class _Expr(Expression):
    __slots__ = ()

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:

        if flags & Flag.MEMOIZE:
            memo = defaultdict(dict)
        else:
            memo = None

        end, args, kwargs = self._match(s, pos, memo)

        if end < 0:
            if memo:
                pos = max(memo)
                args = [_args for _, _args, _ in memo[pos].values()]
            else:
                args = [args]
            if flags & Flag.STRICT:
                exc = _make_parse_error(s, pos, args)
                raise exc
            else:
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
    value_type = Value.ATOMIC

    def __init__(self, pattern: str, flags: int = 0):
        self._re = re.compile(pattern, flags=flags)

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        m = self._re.match(s, pos)
        if not m:
            return FAIL, [(self, pos)], None
        # args = m.groups() if self._re.groups else [m.group(0)]
        args = [m.group(0)]
        return m.end(), args, None


# Combining Expressions,

class Sequence(_Expr):

    __slots__ = 'expressions',
    value_type = Value.ITERABLE

    def __init__(self, *expressions: _Expr):
        self.expressions = list(_pair_bindings(expressions))

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        args = []
        kwargs = {}
        for bind, expr in self.expressions:
            end, _args, _kwargs = expr._match(s, pos, memo)
            if end < 0:
                return FAIL, _args, None
            if bind is not None:
                if _kwargs:
                    kwargs.update(_kwargs)
                if bind:
                    kwargs[bind] = evaluate(_args, expr.value_type)
                else:
                    args.extend(_args)
            pos = end
        return pos, args, kwargs


class Choice(_Expr):

    __slots__ = 'expressions',
    value_type = Value.ITERABLE

    def __init__(self, *expressions: _Expr):
        self.expressions = expressions

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        failargs = []
        for e in self.expressions:
            end, args, kwargs = e._match(s, pos, memo)
            if end >= 0:
                return end, args, kwargs
            failargs.extend(args)
        return FAIL, failargs, None


class Repeat(_Expr):

    __slots__ = 'expression', 'min'
    value_type = Value.ITERABLE

    def __init__(self,
                 expression: _Expr,
                 min: int):
        self.expression = expression
        self.min = min

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        match = self.expression._match
        guard = len(s) - pos  # simple guard against runaway left-recursion

        args = []
        kwargs = {}
        ext = args.extend
        upd = kwargs.update

        end, _args, _kwargs = match(s, pos, memo)
        if end < 0 and self.min > 0:
            return FAIL, (), None
        while end >= 0 and guard > 0:
            ext(_args)
            if _kwargs:
                upd(_kwargs)
            pos = end
            guard -= 1
            end, _args, _kwargs = match(s, pos, memo)

        return pos, args, kwargs


class Star(Repeat):

    __slots__ = ()
    value_type = Value.ITERABLE

    def __init__(self,
                 expression: _Expr):
        super().__init__(expression, 0)


class Plus(Repeat):

    __slots__ = ()
    value_type = Value.ITERABLE

    def __init__(self,
                 expression: _Expr):
        super().__init__(expression, 1)


class Optional(_Expr):

    __slots__ = 'expression',
    value_type = Value.ITERABLE

    def __init__(self, expression: _Expr):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if end < 0:
            return pos, (), None
        return end, args, kwargs


# Non-consuming Expressions

class Lookahead(_Expr):
    """An expression that may match but consumes no input."""

    __slots__ = 'expression', 'polarity',
    value_type = Value.EMPTY

    def __init__(self, expression: _Expr, polarity: bool):
        self.expression = expression
        self.polarity = polarity

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if self.polarity ^ (end >= 0):
            return FAIL, [(self, pos)], None
        return pos, (), None


# Value-changing Expressions

class Raw(_Expr):
    __slots__ = 'expression',
    value_type = Value.ATOMIC

    def __init__(self, expression: _Expr):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, [s[pos:end]], None


class Discard(_Expr):

    __slots__ = 'expression',
    value_type = Value.EMPTY

    def __init__(self, expression: _Expr):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, (), None


class Bind(_Expr):

    __slots__ = 'expression', 'name',
    value_type = Value.EMPTY

    def __init__(self, expression: _Expr, name: str):
        self.expression = expression
        self.name = name

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        if not kwargs:
            kwargs = {}
        kwargs[self.name] = evaluate(args, expr.value_type)
        return end, (), kwargs


# Recursion and Rules

class Rule(_Expr):
    """
    A grammar rule is a named expression with an optional action.

    The *name* field is more relevant for the grammar than the rule
    itself, but it helps with debugging.
    """

    __slots__ = '_expression', '_action', 'name'

    def __init__(self,
                 name: str,
                 expression: Union[_Expr, None],
                 action: Callable = None):
        self.name = name
        self._expression = expression
        self._action = action
        self.finalize()

    def __repr__(self):
        return f'<{type(self).__name__} ({self.name}) object at {id(self)}>'

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

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        _id = id(self)

        if memo and pos in memo and _id in memo[pos]:
            end, args, kwargs = memo[pos][_id]  # packrat memoization check
        else:
            # clear memo beyond size limit
            while memo and len(memo) > MAX_MEMO_SIZE:
                for _pos in sorted(memo)[:DEL_MEMO_SIZE]:
                    del memo[_pos]

            expr = self.expression
            end, args, kwargs = expr._match(s, pos, memo)
            action = self.action
            if end >= 0 and action:
                args = [action(*args, **(kwargs or {}))]

            if memo is not None:
                memo[pos][_id] = (end, args, kwargs)

        return end, args, {}

    def finalize(self):
        if self._expression:
            if self._action is not None:
                self.value_type = Value.ATOMIC
            else:
                self.value_type = self._expression.value_type
        else:
            self.value_type = Value.DEFERRED


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

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        return self._exprs[self.start].match(s, pos=pos, flags=flags)


def _grammar_to_packrat(grammar):
    actns = grammar.actions
    exprs = {}
    for name, _def in grammar.definitions.items():
        expr = _def_to_expr(_def, exprs)
        # TODO: this logic could be improved
        if name not in exprs:
            if name in actns:
                if not isinstance(expr, Rule):
                    expr = Rule(name, expr)
                expr.action = actns[name]
            exprs[name] = expr
        else:
            expr = exprs[name]
            assert isinstance(expr, Rule)
            expr.expression = _def_to_expr(_def, exprs)
            expr.action = actns.get(name, expr.action)

    # ensure all symbols are defined
    for name, expr in exprs.items():
        if expr is None or isinstance(expr, Rule) and expr.expression is None:
            raise Error(f'undefined rule: {name}')
    return exprs


def _def_to_expr(_def: Definition, exprs):
    op = _def.op
    args = _def.args
    if op == Operator.DOT:
        return Terminal('.')
    elif op == Operator.LIT:
        return Terminal(re.escape(args[0]))
    elif op == Operator.CLS:
        s = (args[0]
             .replace('[', '\\[')
             .replace(']', '\\]'))
        return Terminal(f'[{s}]')  # TODO: validate ranges
    elif op == Operator.RGX:
        return Terminal(args[0], flags=args[1])
    elif op == Operator.OPT:
        return Optional(_def_to_expr(args[0], exprs))
    elif op == Operator.STR:
        return Star(_def_to_expr(args[0], exprs))
    elif op == Operator.PLS:
        return Plus(_def_to_expr(args[0], exprs))
    elif op == Operator.SYM:
        return exprs.setdefault(args[0], Rule(args[0], None))
    elif op == Operator.AND:
        return Lookahead(_def_to_expr(args[0], exprs), True)
    elif op == Operator.NOT:
        return Lookahead(_def_to_expr(args[0], exprs), False)
    elif op == Operator.RAW:
        return Raw(_def_to_expr(args[0], exprs))
    elif op == Operator.DIS:
        return Discard(_def_to_expr(args[0], exprs))
    elif op == Operator.BND:
        return Bind(_def_to_expr(args[1], exprs), name=args[0])
    elif op == Operator.SEQ:
        return Sequence(*[_def_to_expr(e, exprs) for e in args[0]])
    elif op == Operator.CHC:
        return Choice(*[_def_to_expr(e, exprs) for e in args[0]])
    elif op == Operator.RUL:
        return Rule('<anonymous>',
                    _def_to_expr(args[0], exprs),
                    action=args[1])
    else:
        raise Error(f'invalid definition: {_def!r}')


def _make_parse_error(s, pos, failures):
    try:
        start = s.rindex('\n', 0, pos)
    except ValueError:
        start = 0
    try:
        end = s.index('\n', start + 1)
    except ValueError:
        end = len(s)
    lineno = s.count('\n', 0, start + 1)
    line = s[start:end]
    failures = ', or '.join(str(pe) for err in failures for pe, _ in err)
    return ParseError(f'failed to parse {failures}',
                      lineno=lineno,
                      offset=pos - start,
                      text=line)


def _pair_bindings(expressions):
    for expr in expressions:
        if isinstance(expr, Bind):
            yield (expr.name, expr.expression)
        elif isinstance(expr, Discard):
            yield (None, expr.expression)
        else:
            yield (False, expr)
