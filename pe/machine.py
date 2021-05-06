
"""
PEG Parsing Machine

Inspired by Medeiros and Ierusalimschy, 2008, "A Parsing Machine for PEGs"

"""

from typing import Union, Tuple, List, Optional, Any
import re

from pe._constants import FAIL, Operator, Flag
from pe._errors import Error
from pe._match import Match
from pe._types import Memo
from pe._grammar import Grammar
from pe._parser import Parser
from pe._optimize import optimize
from pe.actions import Action, Capture, Bind


PASS = 0
BRANCH = 1     # aka Choice
COMMIT = 2
UPDATE = 3     # aka PartialCommit
RESTORE = 4    # aka BackCommit
FAILTWICE = 5
CALL = 6
RETURN = 7
JUMP = 8
MARK = 9       # aka CaptureBegin
APPLY = 10
REGEX = 11
LITERAL = 12
CLASS = 13
DOT = 14
# BIND = 14
# RULE = 15

_Step = Tuple[int, Any, Optional[Action]]  # (opcode, arg, action)
_State = Tuple[int, int, int, int]         # (opidx, pos, argidx, kwargidx)
_Binding = Tuple[str, Any]


class MachineParser(Parser):
    __slots__ = 'grammar', 'pi', '_index',

    def __init__(self, grammar: Grammar,
                 flags: Flag = Flag.NONE):
        super().__init__(grammar, flags=flags)

        grammar = optimize(grammar,
                           inline=flags & Flag.INLINE,
                           regex=flags & Flag.REGEX)
        # if flags & Flag.DEBUG:
        #     grammar = debug(grammar)
        pi, index = _make_program(grammar)
        self.pi: List[_Step] = pi
        self._index = index

    @property
    def start(self):
        return self.grammar.start

    def __contains__(self, name: str) -> bool:
        return name in self._index

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        memo: Union[Memo, None] = None
        end, args, kwargs = self._match(s, pos, memo)
        return Match(s, pos, end, self.grammar[self.start], args, kwargs)

    def _match(self, s: str, pos: int, memo: Optional[Memo]):  # noqa: C901
        pi = self.pi
        stack: List[_State] = [
            (0, 0, 0, 0),    # failure (top-level backtrack entry)
            (-1, -1, 0, 0),  # success
        ]
        args: List[Any] = []
        kwargs: List[_Binding] = []

        idx = self._index[self.start]
        end = -1
        while stack:
            opcode, arg, action = pi[idx]

            if opcode == REGEX:
                m = arg.match(s, pos)
                if m is None:
                    idx = FAIL
                else:
                    end = m.end()

            elif opcode == LITERAL:
                if s.startswith(arg, pos):
                    end = pos + len(arg)
                else:
                    idx = FAIL

            # elif opcode == CLASS:
            #     # chars = arg
            #     try:
            #         if s[pos] in arg:
            #             end = pos + 1
            #             pos = end
            #         else:
            #             idx = FAIL
            #     except IndexError:
            #         idx = FAIL

            elif opcode == DOT:
                try:
                    s[pos]
                except IndexError:
                    idx = FAIL
                else:
                    end = pos + 1

            elif opcode == BRANCH:
                stack.append((idx + arg, pos, len(args), len(kwargs)))
                idx += 1
                continue

            elif opcode == CALL:
                stack.append((idx + 1, -1, stack[-1][2], stack[-1][3]))
                idx = self._index[arg]
                continue

            elif opcode == COMMIT:
                stack.pop()
                idx += arg
                continue

            elif opcode == UPDATE:
                next_idx = stack.pop()[0]
                stack.append((next_idx, pos, len(args), len(kwargs)))
                idx += arg
                continue

            elif opcode == RESTORE:
                pos = stack.pop()[1]
                idx += arg
                continue

            elif opcode == FAILTWICE:
                pos = stack.pop()[1]
                idx = -1

            elif opcode == RETURN:
                idx = stack.pop()[0]
                continue

            elif opcode == APPLY:
                pass
            elif opcode == PASS:
                break
            elif opcode == FAIL:
                idx = FAIL
            else:
                raise Error(f'invalid operation: {opcode}')

            if idx == FAIL:
                n = _n_to_backtrack(stack)
                idx, pos, argidx, kwidx = stack[n]
                stack[n:] = []
                args[argidx:] = []
                if kwargs:
                    kwargs[kwidx:] = []
            else:
                if action:
                    argidx = stack[-1][2]
                    kwidx = stack[-1][3]
                    _args, _kwargs = action(
                        s,
                        pos,
                        end,
                        args[argidx:],
                        dict(kwargs[kwidx:])
                    )
                    args[argidx:] = _args
                    if not _kwargs:
                        kwargs[kwidx:] = []
                    else:
                        kwargs[kwidx:] = _kwargs.items()
                idx += 1
                pos = end

        return pos, args, kwargs


def _n_to_backtrack(stack):
    n = -1
    try:
        while stack[n][1] < 0:
            n -= 1
    except IndexError:
        n += 1
    return n


def _make_program(grammar):
    """A "program" is a set of instructions and mappings."""
    index = {}
    pi = [(FAIL, None, None)]  # special instruction for general failure

    for name in grammar.definitions:
        index[name] = len(pi)
        _pi = _parsing_instructions(grammar[name])
        pi.extend(_pi)
        pi.append((RETURN, None, None))

    pi.append((PASS, None, None))  # success condition

    return pi, index


def _dot(defn, action):
    return [(DOT, None, action)]


def _lit(defn, action):
    return [(LITERAL, defn.args[0], action)]


def _cls(defn, action):
    pat = re.compile(f'[{defn.args[0]}]')
    return [(REGEX, pat, action)]


def _rgx(defn, action):
    pat = re.compile(f'{defn.args[0]}', flags=defn.args[1])
    return [(REGEX, pat, action)]


def _opt(defn, action):
    pi = _parsing_instructions(defn.args[0])
    return [(BRANCH, len(pi) + 2, None),
            *pi,
            (COMMIT, 1, action)]


def _str(defn, action):
    pi = _parsing_instructions(defn.args[0])
    act = [(APPLY, None, action)] if action else []
    return [(BRANCH, len(pi) + 2, None),
            *pi,
            (UPDATE, -len(pi), None)] + act


def _pls(defn, action):
    pi = _parsing_instructions(defn.args[0])
    act = [(APPLY, None, action)] if action else []
    return [*pi,
            (BRANCH, len(pi) + 2, None),
            *pi,
            (UPDATE, -len(pi), None)] + act


def _sym(defn, action):
    return [(CALL, defn.args[0], action)]


def _and(defn, action):
    pi = _parsing_instructions(defn.args[0])
    act = [(APPLY, None, action)] if action else []
    return [(BRANCH, len(pi) + 2 + len(act), None),
            *pi,
            *act,
            (RESTORE, 2, None),
            (FAIL, None, None)]


def _not(defn, action):
    pi = _parsing_instructions(defn.args[0])
    act = [(APPLY, None, action)] if action else []
    return [(BRANCH, len(pi) + 2 + len(act), defn),
            *pi,
            *act,
            (FAILTWICE, None, None)]


def _cap(defn, action):
    if not action:
        action = str
    return _rul(defn.args[0], Capture(action))


def _bnd(defn, action):
    return _rul(defn.args[0], Bind(defn.args[1]))


def _seq(defn, action):
    head = [pi
            for d in defn.args[0][:-1]
            for pi in _parsing_instructions(d)]
    tail = _parsing_instructions(defn.args[0][-1], action)
    return head + tail


def _chc(defn, action):
    # TODO: action
    pis = [_parsing_instructions(d) for d in defn.args[0]]
    pi = pis[-1]
    for _pi in reversed(pis[:-1]):
        pi = [(BRANCH, len(_pi) + 2, None),
              *_pi,
              (COMMIT, len(pi) + 1, None),
              *pi]
    return pi


def _rul(defn, action):
    subdefn, subaction, _ = defn.args
    if not action:
        return _parsing_instructions(subdefn, subaction)
    elif not subaction:
        return _parsing_instructions(subdefn, action)
    else:
        return (_parsing_instructions(subdefn, subaction)
                + [(APPLY, None, action)])


_op_map = {
    Operator.DOT: _dot,
    Operator.LIT: _lit,
    Operator.CLS: _cls,
    Operator.RGX: _rgx,
    Operator.OPT: _opt,
    Operator.STR: _str,
    Operator.PLS: _pls,
    Operator.SYM: _sym,
    Operator.AND: _and,
    Operator.NOT: _not,
    Operator.CAP: _cap,
    Operator.BND: _bnd,
    Operator.SEQ: _seq,
    Operator.CHC: _chc,
    Operator.RUL: _rul,
}


def _parsing_instructions(defn, action=None):  # noqa: C901
    try:
        return _op_map[defn.op](defn, action)
    except KeyError:
        raise Error(f'invalid definition: {defn!r}')
