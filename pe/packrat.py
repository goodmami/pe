
"""
Packrat Parsing

"""

# NOTE: attempting to use exceptions instead of FAIL codes resulted in
# almost a 2x slowdown, so it's probably not a good idea

from typing import (Union, Dict, Callable)
from collections import defaultdict
import re

from pe._constants import (
    FAIL,
    MAX_MEMO_SIZE,
    DEL_MEMO_SIZE,
    Operator,
    Value,
    Flag,
)
from pe._errors import Error, ParseFailure, ParseError
from pe._definition import Definition
from pe._match import Match, evaluate
from pe._types import RawMatch, Memo
from pe._grammar import Grammar
from pe._parser import Parser
from pe._optimize import optimize


_Matcher = Callable[[str, int, Flag], RawMatch]


# Terms (Dot, Literal, Class)

def Terminal(definition: Definition) -> _Matcher:

    op = definition.op
    if op == Operator.DOT:
        _re = re.compile('.')
    elif op == Operator.LIT:
        _re = re.compile(re.escape(definition.args[0]))
    elif op == Operator.CLS:
        s = (definition.args[0]
             .replace('[', '\\[')
             .replace(']', '\\]'))
        _re = re.compile(f'[{s}]')  # TODO: validate ranges
    elif op == Operator.RGX:
        _re = re.compile(definition.args[0], flags=definition.args[1])

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        m = _re.match(s, pos)
        if m:
            retval = m.end(), (), None
        else:
            retval = FAIL, (pos, definition), None
            if memo is not None:
                memo[pos][id(definition)] = retval
        return retval

    return _match


# Combining Expressions,

def Sequence(definitions: Definition, exprs) -> _Matcher:

    expressions = [_def_to_expr(defn, exprs) for defn in definitions]

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        args = []
        kwargs = {}
        for expr in expressions:
            end, _args, _kwargs = expr(s, pos, memo)
            if end < 0:
                return FAIL, _args, None
            else:
                args.extend(_args)
                if _kwargs:
                    kwargs.update(_kwargs)
                pos = end
        return pos, tuple(args), kwargs

    return _match


def Choice(definitions: Definition, exprs) -> _Matcher:

    expressions = [_def_to_expr(defn, exprs) for defn in definitions]

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        _id = id(_match)

        if memo and pos in memo and _id in memo[pos]:
            end, args, kwargs = memo[pos][_id]  # packrat memoization check
        else:
            # clear memo beyond size limit
            if memo and len(memo) > MAX_MEMO_SIZE:
                for _pos in sorted(memo)[:DEL_MEMO_SIZE]:
                    del memo[_pos]
            for e in expressions:
                end, args, kwargs = e(s, pos, memo)
                if end >= 0:
                    break
            if memo is not None:
                memo[pos][_id] = (end, args, kwargs)

        return end, args, kwargs  # end may be FAIL

    return _match


def Repeat(definition: Definition, min: int, exprs) -> _Matcher:

    expression = _def_to_expr(definition, exprs)

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        guard = len(s) - pos  # simple guard against runaway left-recursion

        args = []
        kwargs = {}
        ext = args.extend
        upd = kwargs.update

        end, _args, _kwargs = expression(s, pos, memo)
        if end < 0 and min > 0:
            return FAIL, _args, None
        while end >= 0 and guard > 0:
            ext(_args)
            if _kwargs:
                upd(_kwargs)
            pos = end
            guard -= 1
            end, _args, _kwargs = expression(s, pos, memo)

        return pos, args, kwargs

    return _match


def Optional(definition: Definition, exprs: Dict[str, _Matcher]) -> _Matcher:

    expression = _def_to_expr(definition, exprs)

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = expression(s, pos, memo)
        if end < 0:
            return pos, (), None
        return end, args, kwargs

    return _match


# Non-consuming Expressions

def Lookahead(definition: Definition, polarity: bool, exprs) -> _Matcher:
    """An expression that may match but consumes no input."""

    expression = _def_to_expr(definition, exprs)

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = expression(s, pos, memo)
        passed = end >= 0
        if polarity ^ passed:
            if passed:  # negative lookahead failed
                return FAIL, (pos, expression), None
            else:       # positive lookahead failed
                return FAIL, args, None
        return pos, (), None

    return _match


# Value-changing Expressions

def Raw(definition: Definition, exprs) -> _Matcher:

    expression = _def_to_expr(definition, exprs)

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = expression(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        return end, (s[pos:end],), None

    return _match


def Bind(name, definition: Definition, exprs) -> _Matcher:

    expr_value = definition.value
    expression = _def_to_expr(definition, exprs)

    def _match(s: str, pos: int, memo: Memo) -> RawMatch:
        end, args, kwargs = expression(s, pos, memo)
        if end < 0:
            return FAIL, args, None
        if not kwargs:
            kwargs = {}
        kwargs[name] = evaluate(args, expr_value)
        return end, (), kwargs

    return _match


# Recursion and Rules

class Rule:
    """
    A grammar rule is a named expression with an optional action.

    The *name* field is more relevant for the grammar than the rule
    itself, but it helps with debugging.
    """
    def __init__(self,
                 name: str,
                 definition: Union[Definition, None],
                 action: Union[Callable, None],
                 exprs):
        self.name = name
        self.expression: _Matcher = None
        if definition:
            self.expression = _def_to_expr(definition, exprs)
        self.action = action

    def set_expression(self, expression: _Matcher):
        self.expression = expression

    def __call__(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expression = self.expression

        if expression:
            end, args, kwargs = expression(s, pos, memo)
            action = self.action
            if end >= 0 and action:
                try:
                    args = [action(*args, **(kwargs or {}))]
                except ParseFailure as exc:
                    raise _make_parse_error(
                        s, pos, exc.message
                    ).with_traceback(exc.__traceback__)
            return end, args, {}
        else:
            raise NotImplementedError


class PackratParser(Parser):

    def __init__(self, grammar: Union[Grammar, Definition],
                 flags: Flag = Flag.NONE):
        super().__init__(grammar, flags=flags)
        self._exprs: Dict[str, Callable] = _grammar_to_packrat(
            grammar, flags)

    @property
    def start(self):
        return self.grammar.start

    def __contains__(self, name: str) -> bool:
        return name in self._exprs

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.MEMOIZE | Flag.STRICT) -> Union[Match, None]:
        memo: Union[Memo, None] = None
        if flags & Flag.MEMOIZE:
            memo = defaultdict(dict)

        end, args, kwargs = self._exprs[self.start](s, pos, memo)

        if end < 0:
            if flags & Flag.STRICT:
                failpos, message = _get_furthest_fail(args, memo)
                exc = _make_parse_error(s, failpos, message)
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
            if isinstance(expr, Rule):
                action = expr.action
                expr = expr.expression
            else:
                action = None
            exprs[name].expression = expr
            exprs[name].action = action
        else:
            exprs[name] = expr

    # ensure all symbols are defined
    for name, expr in exprs.items():
        if expr is None or (isinstance(expr, Rule)
                            and expr.expression is None):
            raise Error(f'undefined rule: {name}')
    return exprs


def _def_to_expr(_def: Definition, exprs):
    op = _def.op
    args = _def.args
    if op in (Operator.DOT, Operator.LIT, Operator.CLS, Operator.RGX):
        return Terminal(_def)
    elif op == Operator.OPT:
        return Optional(args[0], exprs)
        # return Optional(_def_to_expr(args[0], exprs), val)
    elif op == Operator.STR:
        return Repeat(args[0], 0, exprs)
    elif op == Operator.PLS:
        return Repeat(args[0], 1, exprs)
    elif op == Operator.SYM:
        return exprs.setdefault(args[0], Rule(args[0], None, None, exprs))
    elif op == Operator.AND:
        return Lookahead(args[0], True, exprs)
    elif op == Operator.NOT:
        return Lookahead(args[0], False, exprs)
    elif op == Operator.RAW:
        return Raw(args[0], exprs)
    elif op == Operator.BND:
        return Bind(args[1], args[0], exprs)
    elif op == Operator.SEQ:
        return Sequence(args[0], exprs)
    elif op == Operator.CHC:
        return Choice(args[0], exprs)
    elif op == Operator.RUL:
        _def, action, name = args
        return Rule(name, _def, action, exprs)
    else:
        raise Error(f'invalid definition: {_def!r}')


def _get_furthest_fail(args, memo):
    failpos, defn = args
    message = str(defn)
    # assuming we're here because of a failure, the max memo position
    # should be the furthest failure
    if memo:
        memopos = max(memo)
        fails = []
        if memopos > failpos:
            fails = [args[1]
                     for pos, args, _
                     in memo[memopos].values()
                     if pos < 0]
        if fails:
            failpos = memopos
            message = ', '.join(map(str, fails))
    return failpos, message


def _make_parse_error(s, pos, message):
    try:
        start = s.rindex('\n', 0, pos) + 1
    except ValueError:
        start = 0
    try:
        end = s.index('\n', start)
    except ValueError:
        end = len(s)
    lineno = s.count('\n', 0, start)
    line = s[start:end]
    return ParseError(message,
                      lineno=lineno,
                      offset=pos - start,
                      text=line)
