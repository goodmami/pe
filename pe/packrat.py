
"""
Packrat Parsing

"""

from typing import (
    Union, Tuple, Sequence, Dict, Callable, Pattern)
import re
from collections import defaultdict

from pe.constants import FAIL, Operator, ValueType, Flag
from pe.core import (
    Error,
    ParseError,
    Match,
    Expression,
    Definition,
    Grammar,
)

_MatchResult = Tuple[int, Sequence, Union[Dict, None]]
Memo = Dict[int, Dict[int, _MatchResult]]

#: Number of string positions that can be cached at one time.
MAX_MEMO_SIZE = 1000


class _Expr(Expression):
    __slots__ = ()

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
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

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        raise NotImplementedError()


# Terms (Dot, Literal, Class)

class Terminal(_Expr):
    """An atomic expression."""

    __slots__ = '_re',

    def __init__(self, pattern: str, flags: int = 0):
        self._re = re.compile(pattern, flags=flags)
        if self._re.groups == 0:
            self.value_type = ValueType.MONADIC
        else:
            self.value_type = ValueType.VARIADIC

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        m = self._re.match(s, pos)
        if not m:
            return FAIL, [(self, pos)], None
        args = m.groups() if self._re.groups else [m.group(0)]
        return m.end(), args, None


# Combining Expressions,

class Sequence(_Expr):

    __slots__ = 'expressions',
    value_type = ValueType.VARIADIC

    def __init__(self, *expressions: _Expr):
        self.expressions = expressions

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        args = []
        kwargs = {}
        for expression in self.expressions:
            end, _args, _kwargs = expression._match(s, pos, memo)
            if end < 0:
                return FAIL, _args, None
            args.extend(_args)
            if _kwargs:
                kwargs.update(_kwargs)
            pos = end
        return pos, args, kwargs


class Choice(_Expr):

    __slots__ = 'expressions',
    value_type = ValueType.VARIADIC

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

    __slots__ = 'expression', 'min', 'max',
    value_type = ValueType.VARIADIC

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
            return FAIL, [(self, pos)], None
        return pos, args, kwargs


class Optional(_Expr):

    __slots__ = 'expression',
    value_type = ValueType.VARIADIC

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
    value_type = ValueType.NILADIC

    def __init__(self, expression: _Expr, polarity: bool):
        self.expression = expression
        self.polarity = polarity

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if self.polarity ^ (end >= 0):
            return FAIL, args, None
        return pos, (), None


# Value-changing Expressions

class Raw(_Expr):

    __slots__ = 'expression',
    value_type = ValueType.MONADIC

    def __init__(self, expression: _Expr):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        end, args, kwargs = self.expression._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, (s[pos:end],), None


class Bind(_Expr):

    __slots__ = 'expression', 'name',
    value_type = ValueType.NILADIC

    def __init__(self, expression: _Expr, name: str = None):
        self.expression = expression
        self.name = name

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        expr = self.expression
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        name = self.name
        if name:
            value_type = expr.value_type
            if not kwargs:
                kwargs = {}
            if value_type == ValueType.NILADIC:
                kwargs[name] = None
            elif value_type == ValueType.MONADIC:
                kwargs[name] = args[0]
            elif value_type == ValueType.VARIADIC:
                kwargs[name] = args
            else:
                raise Error(
                    'cannot bind {expr!r} with value type {value_type!r}')
        return end, (), kwargs


class Evaluate(_Expr):

    __slots__ = 'expression',
    value_type = ValueType.MONADIC

    def __init__(self, expression: _Expr):
        self.expression = expression

    def _match(self, s: str, pos: int, memo: Memo) -> _MatchResult:
        expr = self.expression
        value_type = expr.value_type
        end, args, kwargs = expr._match(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        if value_type == ValueType.NILADIC:
            arg = None
        elif value_type == ValueType.MONADIC:
            arg = args[0]
        elif value_type == ValueType.VARIADIC:
            arg = args
        else:
            raise Error(
                f'cannot evaluate {expr!r} with value type {value_type!r}')
        return end, [args], None


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

        if pos in memo and _id in memo[pos]:
            end, args, kwargs = memo[pos][_id]  # packrat memoization check
        else:
            # clear memo beyond size limit
            while len(memo) > MAX_MEMO_SIZE:
                del memo[min(memo)]

            expr = self.expression
            end, args, kwargs = expr._match(s, pos, memo)
            if end >= 0 and self.action:
                args = [self.action(*args, **(kwargs or {}))]

            memo[pos][_id] = (end, args, kwargs)

        return end, args, {}

    def finalize(self):
        if self._expression:
            if self._action is not None:
                self.value_type = ValueType.MONADIC
            else:
                self.value_type = self._expression.value_type
        else:
            self.value_type = ValueType.DEFERRED


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
    defns = grammar.definitions
    actns = grammar.actions
    exprs = {}
    for name, _def in defns.items():
        if name not in exprs:
            expr = _def_to_expr(_def, defns, exprs)
            if name in actns:
                expr = Rule(name, expr, action=actns[name])
            exprs[name] = expr
        else:
            expr = exprs[name]
            if isinstance(expr, Rule) and expr.expression is None:
                expr.expression = _def_to_expr(_def, defns, exprs)
            expr.action = actns.get(name)
    # ensure all symbols are defined
    for name, expr in exprs.items():
        if expr is None or isinstance(expr, Rule) and expr.expression is None:
            raise Error(f'undefined rule: {name}')
    return exprs


def _def_to_expr(_def: Definition, defns, exprs):
    op = _def.op
    args = _def.args
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
        return exprs.setdefault(args[0], Rule(args[0], None))
    elif op == Operator.AND:
        return Lookahead(_def_to_expr(args[0], defns, exprs), True)
    elif op == Operator.NOT:
        return Lookahead(_def_to_expr(args[0], defns, exprs), False)
    elif op == Operator.RAW:
        return Raw(_def_to_expr(args[0], defns, exprs))
    elif op == Operator.BND:
        return Bind(_def_to_expr(args[1], defns, exprs), name=args[0])
    elif op == Operator.EVL:
        return Evaluate(_def_to_expr(args[0], defns, exprs))
    elif op == Operator.SEQ:
        return Sequence(*[_def_to_expr(e, defns, exprs) for e in args[0]])
    elif op == Operator.CHC:
        return Choice(*[_def_to_expr(e, defns, exprs) for e in args[0]])
    elif op == Operator.RUL:
        return Rule('<anonymous>',
                    _def_to_expr(args[0], defns, exprs),
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
