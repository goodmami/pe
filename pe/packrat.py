
"""
Packrat Parsing

"""

# NOTE: attempting to use exceptions instead of FAIL codes resulted in
# almost a 2x slowdown, so it's probably not a good idea

from typing import (Union, List, Dict, Callable, Iterable, Any)
from collections import defaultdict
import re

from pe._constants import (
    FAIL,
    MAX_MEMO_SIZE,
    DEL_MEMO_SIZE,
    Operator,
    Flag,
)
from pe._errors import Error, ParseFailure, ParseError
from pe._definition import Definition
from pe._match import Match, determine
from pe._types import RawMatch, Memo
from pe._grammar import Grammar
from pe._parser import Parser
from pe._optimize import optimize
from pe.actions import Action, Call


_Matcher = Callable[[str, int, Memo], RawMatch]


class PackratParser(Parser):

    def __init__(self, grammar: Union[Grammar, Definition],
                 flags: Flag = Flag.NONE):
        if isinstance(grammar, Definition):
            grammar = Grammar({'Start': grammar})
        if not grammar.final:
            grammar.finalize()
        super().__init__(grammar, flags=flags)

        grammar = optimize(grammar,
                           inline=flags & Flag.INLINE,
                           regex=flags & Flag.REGEX)

        self._exprs: Dict[str, Callable] = {}
        self._grammar_to_packrat(grammar)

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

    def _grammar_to_packrat(self, grammar):
        exprs = self._exprs
        for name, _def in grammar.definitions.items():
            expr = self._def_to_expr(_def)
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
                exprs[name].set_action(action)
            else:
                exprs[name] = expr

        # ensure all symbols are defined
        for name, expr in exprs.items():
            if expr is None or (isinstance(expr, Rule)
                                and expr.expression is None):
                raise Error(f'undefined rule: {name}')
        return exprs

    def _def_to_expr(self, definition: Definition):
        op = definition.op
        if op == Operator.SYM:
            name = definition.args[0]
            return self._exprs.setdefault(name, Rule(name, None, None))
        else:
            try:
                meth = self._op_map[op]
            except KeyError:
                raise Error(f'invalid definition: {definition!r}')
            else:
                return meth(self, definition)

    def _terminal(self, definition: Definition) -> _Matcher:

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
            retval: RawMatch
            if m:
                retval = m.end(), (), None
            else:
                retval = FAIL, (pos, definition), None
                if memo is not None:
                    memo[pos][id(_match)] = retval
            return retval

        return _match

    def _sequence(self, definition: Definition) -> _Matcher:

        items: Iterable[Definition] = definition.args[0]
        expressions = [self._def_to_expr(defn) for defn in items]

        def _match(s: str, pos: int, memo: Memo) -> RawMatch:
            args: List = []
            kwargs: Dict[str, Any] = {}
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

    def _choice(self, definition: Definition) -> _Matcher:

        items: Iterable[Definition] = definition.args[0]
        expressions = [self._def_to_expr(defn) for defn in items]

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

    def _repeat(self, definition: Definition, min: int) -> _Matcher:

        expression = self._def_to_expr(definition)

        def _match(s: str, pos: int, memo: Memo) -> RawMatch:
            guard = len(s) - pos  # simple guard against runaway left-recursion

            args: List = []
            kwargs: Dict[str, Any] = {}
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

            return pos, tuple(args), kwargs

        return _match

    def _star(self, definition: Definition) -> _Matcher:
        return self._repeat(definition.args[0], 0)

    def _plus(self, definition: Definition) -> _Matcher:
        return self._repeat(definition.args[0], 1)

    def _optional(self, definition: Definition) -> _Matcher:

        expression = self._def_to_expr(definition.args[0])

        def _match(s: str, pos: int, memo: Memo) -> RawMatch:
            end, args, kwargs = expression(s, pos, memo)
            if end < 0:
                return pos, (), None
            return end, args, kwargs

        return _match

    def _lookahead(self, definition: Definition, polarity: bool) -> _Matcher:
        """An expression that may match but consumes no input."""

        expression = self._def_to_expr(definition)

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

    def _and(self, definition: Definition) -> _Matcher:
        return self._lookahead(definition.args[0], True)

    def _not(self, definition: Definition) -> _Matcher:
        return self._lookahead(definition.args[0], False)

    def _raw(self, definition: Definition) -> _Matcher:
        expression = self._def_to_expr(definition.args[0])

        def _match(s: str, pos: int, memo: Memo) -> RawMatch:
            end, args, kwargs = expression(s, pos, memo)
            if end < 0:
                return FAIL, args, None
            return end, (s[pos:end],), None

        return _match

    def _bind(self, definition: Definition) -> _Matcher:
        bound: Definition = definition.args[0]
        expression = self._def_to_expr(bound)
        name: str = definition.args[1]

        def _match(s: str, pos: int, memo: Memo) -> RawMatch:
            end, args, kwargs = expression(s, pos, memo)
            if end < 0:
                return FAIL, args, None
            if not kwargs:
                kwargs = {}
            kwargs[name] = determine(args)
            return end, (), kwargs

        return _match

    def _rule(self, definition: Definition) -> _Matcher:
        subdef: Definition
        action: Union[Callable, None]
        name: str
        subdef, action, name = definition.args
        expression = self._def_to_expr(subdef)
        return Rule(name, expression, action)

    _op_map = {
        Operator.DOT: _terminal,
        Operator.LIT: _terminal,
        Operator.CLS: _terminal,
        Operator.RGX: _terminal,
        # Operator.SYM: _,
        Operator.OPT: _optional,
        Operator.STR: _star,
        Operator.PLS: _plus,
        Operator.AND: _and,
        Operator.NOT: _not,
        Operator.RAW: _raw,
        Operator.BND: _bind,
        Operator.SEQ: _sequence,
        Operator.CHC: _choice,
        Operator.RUL: _rule,
    }


# Recursion and Rules

class Rule:
    """
    A grammar rule is a named expression with an optional action.

    The *name* field is more relevant for the grammar than the rule
    itself, but it helps with debugging.
    """
    def __init__(self,
                 name: str,
                 expression: Union[_Matcher, None],
                 action: Union[Callable, None]):
        self.name = name
        self.expression = expression
        self.action = None
        if action:
            self.set_action(action)

    def set_action(self, action):
        if action and not isinstance(action, Action):
            action = Call(action)
        self.action = action

    def __call__(self, s: str, pos: int, memo: Memo) -> RawMatch:
        expression = self.expression

        if expression:
            end, args, kwargs = expression(s, pos, memo)
            action = self.action
            if end >= 0 and action:
                if not kwargs:
                    kwargs = {}
                try:
                    args, kwargs = action(s, pos, end, args, kwargs)
                except ParseFailure as exc:
                    raise _make_parse_error(
                        s, pos, exc.message
                    ).with_traceback(exc.__traceback__)
            return end, args, kwargs
        else:
            raise NotImplementedError


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
