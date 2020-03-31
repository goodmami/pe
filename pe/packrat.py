
"""
Packrat Parsing

"""

from typing import (
    Union, Dict, Callable)
import re

from pe._constants import (
    FAIL,
    ANONYMOUS,
    MAX_MEMO_SIZE,
    DEL_MEMO_SIZE,
    Operator,
    Value,
    Flag,
)
from pe._errors import Error, ParseError
from pe._definition import Definition
from pe._match import Match, evaluate
from pe._types import RawMatch, Memo
from pe._grammar import Grammar
from pe._parser import Parser
from pe._optimize import optimize


class Expression:
    """A compiled parsing expression."""

    __slots__ = 'value',

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        memo: Union[Memo, None] = None
        if flags & Flag.MEMOIZE:
            memo = defaultdict(dict)

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

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        raise NotImplementedError()


# Terms (Dot, Literal, Class)

class Terminal(Expression):
    """An atomic expression."""

    __slots__ = '_re',

    def __init__(self, pattern: str, flags: int, value: Value):
        self._re = re.compile(pattern, flags=flags)
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        m = self._re.match(s, pos)
        if not m:
            return FAIL, [(self, pos)], None
        # args = m.groups() if self._re.groups else [m.group(0)]
        args = [m.group(0)]
        return m.end(), args, None


# Combining Expressions,

class Sequence(Expression):

    __slots__ = 'expressions',

    def __init__(self, expressions: Expression, value: Value):
        self.expressions = list(_pair_bindings(expressions))
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
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
                    kwargs[bind] = evaluate(_args, expr.value)
                else:
                    args.extend(_args)
            pos = end
        return pos, args, kwargs


class Choice(Expression):

    __slots__ = 'expressions',

    def __init__(self, expressions: Expression, value: Value):
        self.expressions = expressions
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        failargs = []
        for e in self.expressions:
            end, args, kwargs = e._match(s, pos, memo)
            if end >= 0:
                return end, args, kwargs
            failargs.extend(args)
        return FAIL, failargs, None


class Repeat(Expression):

    __slots__ = 'expression', 'min'

    def __init__(self,
                 expression: Expression,
                 min: int,
                 value: Value):
        self.expression = expression
        self.min = min
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
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


class Optional(Expression):

    __slots__ = 'expression',

    def __init__(self, expression: Expression, value: Value):
        self.expression = expression
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if end < 0:
            return pos, (), None
        return end, args, kwargs


# Non-consuming Expressions

class Lookahead(Expression):
    """An expression that may match but consumes no input."""

    __slots__ = 'expression', 'polarity',

    def __init__(self, expression: Expression, polarity: bool, value: Value):
        self.expression = expression
        self.polarity = polarity
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if self.polarity ^ (end >= 0):
            return FAIL, [(self, pos)], None
        return pos, (), None


# Value-changing Expressions

class Raw(Expression):
    __slots__ = 'expression',

    def __init__(self, expression: Expression, value: Value):
        self.expression = expression
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, [s[pos:end]], None


class Discard(Expression):

    __slots__ = 'expression',

    def __init__(self, expression: Expression, value: Value):
        self.expression = expression
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, (), None


class Bind(Expression):

    __slots__ = 'expression', 'name',

    def __init__(self, expression: Expression, name: str, value: Value):
        self.expression = expression
        self.name = name
        self.value = value

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        if not kwargs:
            kwargs = {}
        kwargs[self.name] = evaluate(args, expr.value)
        return end, (), kwargs


# Recursion and Rules

class Rule(Expression):
    """
    A grammar rule is a named expression with an optional action.

    The *name* field is more relevant for the grammar than the rule
    itself, but it helps with debugging.
    """

    __slots__ = 'expression', 'action', 'name'

    def __init__(self,
                 expression: Union[Expression, None],
                 action: Union[Callable, None],
                 name: str,
                 value: Value):
        self.name = name
        self.expression = expression
        self.action = action
        self.value = value

    def __repr__(self):
        return f'<{type(self).__name__} ({self.name}) object at {id(self)}>'

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
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


class PackratParser(Parser):

    def __init__(self, grammar: Union[Grammar, Definition],
                 flags: Flag = Flag.NONE):
        super().__init__(grammar, flags=flags)
        self._exprs: Dict[str, Expression] = _grammar_to_packrat(
            grammar, flags)

    @property
    def start(self):
        return self.grammar.start

    def __contains__(self, name: str) -> bool:
        return name in self._exprs

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        memo: Union[Memo, None] = None
        if flags & Flag.MEMOIZE:
            memo = defaultdict(dict)

        end, args, kwargs = self._exprs[self.start]._match(s, pos, memo)

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

        return Match(s, pos, end, self.grammar[self.start], args, kwargs)


def _grammar_to_packrat(grammar, flags):
    if isinstance(grammar, Definition):
        grammar = Grammar({'Start': grammar})
    if not grammar.final:
        grammar.finalize()

    grammar = optimize(grammar,
                       inline=flags & Flag.INLINE,
                       regex=flags & Flag.REGEX)

    exprs = {}
    for name, _def in grammar.definitions.items():
        expr = _def_to_expr(_def, exprs)
        # if name is already in exprs, that means it was seen as a
        # nonterminal in some other rule, so don't replace the object
        # or the call chain will break.
        if name in exprs:
            existing = exprs[name]
            if isinstance(expr, Rule):
                existing.expression = expr.expression
                existing.action = expr.action
            else:
                existing.expression = expr
        else:
            exprs[name] = expr

    # ensure all symbols are defined
    for name, expr in exprs.items():
        if expr is None or isinstance(expr, Rule) and expr.expression is None:
            raise Error(f'undefined rule: {name}')
    return exprs


def _def_to_expr(_def: Definition, exprs):
    op = _def.op
    args = _def.args
    val = _def.value
    if op == Operator.DOT:
        return Terminal('.', 0, val)
    elif op == Operator.LIT:
        return Terminal(re.escape(args[0]), 0, val)
    elif op == Operator.CLS:
        s = (args[0]
             .replace('[', '\\[')
             .replace(']', '\\]'))
        return Terminal(f'[{s}]', 0, val)  # TODO: validate ranges
    elif op == Operator.RGX:
        return Terminal(args[0], args[1], val)
    elif op == Operator.OPT:
        return Optional(_def_to_expr(args[0], exprs), val)
    elif op == Operator.STR:
        return Repeat(_def_to_expr(args[0], exprs), 0, val)
    elif op == Operator.PLS:
        return Repeat(_def_to_expr(args[0], exprs), 1, val)
    elif op == Operator.SYM:
        return exprs.setdefault(args[0], Rule(None, None, args[0], val))
    elif op == Operator.AND:
        return Lookahead(_def_to_expr(args[0], exprs), True, val)
    elif op == Operator.NOT:
        return Lookahead(_def_to_expr(args[0], exprs), False, val)
    elif op == Operator.RAW:
        return Raw(_def_to_expr(args[0], exprs), val)
    elif op == Operator.DIS:
        return Discard(_def_to_expr(args[0], exprs), val)
    elif op == Operator.BND:
        return Bind(_def_to_expr(args[0], exprs), args[1], val)
    elif op == Operator.SEQ:
        return Sequence([_def_to_expr(e, exprs) for e in args[0]], val)
    elif op == Operator.CHC:
        return Choice([_def_to_expr(e, exprs) for e in args[0]], val)
    elif op == Operator.RUL:
        _def, action, name = args
        return Rule(_def_to_expr(_def, exprs), action, name, val)
    else:
        raise Error(f'invalid definition: {_def!r}')


def _pair_bindings(expressions):
    for expr in expressions:
        if isinstance(expr, Bind):
            yield (expr.name, expr.expression)
        elif isinstance(expr, Discard):
            yield (None, expr.expression)
        else:
            yield (False, expr)


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
