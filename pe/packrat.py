
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
from pe._core import (
    Error,
    Match,
    RawMatch,
    Memo,
    Expression,
    evaluate,
)
from pe.operators import (
    Definition,
    Grammar,
)
from pe import inline, regex


# Terms (Dot, Literal, Class)

class Terminal(Expression):
    """An atomic expression."""

    __slots__ = '_re',
    value_type = Value.ATOMIC

    def __init__(self, pattern: str, flags: int = 0):
        self._re = re.compile(pattern, flags=flags)

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
    value_type = Value.ITERABLE

    def __init__(self, *expressions: Expression):
        self.expressions = list(_pair_bindings(expressions))

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
                    kwargs[bind] = evaluate(_args, expr.value_type)
                else:
                    args.extend(_args)
            pos = end
        return pos, args, kwargs


class Choice(Expression):

    __slots__ = 'expressions',
    value_type = Value.ITERABLE

    def __init__(self, *expressions: Expression):
        self.expressions = expressions

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
    value_type = Value.ITERABLE

    def __init__(self,
                 expression: Expression,
                 min: int):
        self.expression = expression
        self.min = min

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


class Star(Repeat):

    __slots__ = ()
    value_type = Value.ITERABLE

    def __init__(self,
                 expression: Expression):
        super().__init__(expression, 0)


class Plus(Repeat):

    __slots__ = ()
    value_type = Value.ITERABLE

    def __init__(self,
                 expression: Expression):
        super().__init__(expression, 1)


class Optional(Expression):

    __slots__ = 'expression',
    value_type = Value.ITERABLE

    def __init__(self, expression: Expression):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if end < 0:
            return pos, (), None
        return end, args, kwargs


# Non-consuming Expressions

class Lookahead(Expression):
    """An expression that may match but consumes no input."""

    __slots__ = 'expression', 'polarity',
    value_type = Value.EMPTY

    def __init__(self, expression: Expression, polarity: bool):
        self.expression = expression
        self.polarity = polarity

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if self.polarity ^ (end >= 0):
            return FAIL, [(self, pos)], None
        return pos, (), None


# Value-changing Expressions

class Raw(Expression):
    __slots__ = 'expression',
    value_type = Value.ATOMIC

    def __init__(self, expression: Expression):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, [s[pos:end]], None


class Discard(Expression):

    __slots__ = 'expression',
    value_type = Value.EMPTY

    def __init__(self, expression: Expression):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, (), None


class Bind(Expression):

    __slots__ = 'expression', 'name',
    value_type = Value.EMPTY

    def __init__(self, expression: Expression, name: str):
        self.expression = expression
        self.name = name

    def _match(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        if not kwargs:
            kwargs = {}
        kwargs[self.name] = evaluate(args, expr.value_type)
        return end, (), kwargs


# Recursion and Rules

class Rule(Expression):
    """
    A grammar rule is a named expression with an optional action.

    The *name* field is more relevant for the grammar than the rule
    itself, but it helps with debugging.
    """

    __slots__ = '_expression', '_action', 'name'

    def __init__(self,
                 expression: Union[Expression, None],
                 action: Callable = None,
                 name: str = ANONYMOUS):
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
    def expression(self, expression: Expression):
        self._expression = expression
        self.finalize()

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, action: Union[Callable, None]):
        self._action = action
        self.finalize()

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

    def finalize(self):
        if self._expression:
            if self._action is not None:
                self.value_type = Value.ATOMIC
            else:
                self.value_type = self._expression.value_type
        else:
            self.value_type = Value.DEFERRED


class PackratParser(Expression):

    __slots__ = 'grammar', 'flags', '_exprs',

    def __init__(self, grammar: Union[Grammar, Definition],
                 flags: Flag = Flag.NONE):
        if isinstance(grammar, Definition):
            grammar = Grammar({'Start': grammar})
        self.grammar = grammar
        self.flags = flags
        self._exprs: Dict[str, Expression] = _grammar_to_packrat(
            grammar, flags)

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


def _grammar_to_packrat(grammar, flags):
    if not grammar.final:
        grammar.finalize()

    if flags & Flag.INLINE:
        grammar = inline.optimize(grammar)
    if flags & Flag.REGEX:
        grammar = regex.optimize(grammar)

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
        return exprs.setdefault(args[0], Rule(None, None, name=args[0]))
    elif op == Operator.AND:
        return Lookahead(_def_to_expr(args[0], exprs), True)
    elif op == Operator.NOT:
        return Lookahead(_def_to_expr(args[0], exprs), False)
    elif op == Operator.RAW:
        return Raw(_def_to_expr(args[0], exprs))
    elif op == Operator.DIS:
        return Discard(_def_to_expr(args[0], exprs))
    elif op == Operator.BND:
        return Bind(_def_to_expr(args[0], exprs), name=args[1])
    elif op == Operator.SEQ:
        return Sequence(*[_def_to_expr(e, exprs) for e in args[0]])
    elif op == Operator.CHC:
        return Choice(*[_def_to_expr(e, exprs) for e in args[0]])
    elif op == Operator.RUL:
        _def, action, name = args
        return Rule(_def_to_expr(_def, exprs),
                    action=action,
                    name=name)
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
