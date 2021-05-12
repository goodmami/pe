
"""
PEG Parsing Machine

Inspired by Medeiros and Ierusalimschy, 2008, "A Parsing Machine for PEGs"

"""

from typing import Union, Tuple, List, Optional, Any, NamedTuple
import re
from enum import IntEnum

from pe._constants import FAIL as FAILURE, Operator, Flag
from pe._errors import Error
from pe._match import Match
from pe._types import Memo
from pe._grammar import Grammar
from pe._parser import Parser
from pe._optimize import optimize
from pe.actions import Action, Capture, Bind
from pe.operators import Rule


class OpCode(IntEnum):
    FAIL = -1
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


# Alias these for performance and convenience
FAIL = OpCode.FAIL
PASS = OpCode.PASS
BRANCH = OpCode.BRANCH
COMMIT = OpCode.COMMIT
UPDATE = OpCode.UPDATE
RESTORE = OpCode.RESTORE
FAILTWICE = OpCode.FAILTWICE
CALL = OpCode.CALL
RETURN = OpCode.RETURN
JUMP = OpCode.JUMP
MARK = OpCode.MARK
APPLY = OpCode.APPLY
REGEX = OpCode.REGEX
LITERAL = OpCode.LITERAL
CLASS = OpCode.CLASS
DOT = OpCode.DOT


class Instruction(NamedTuple):
    opcode: OpCode                   # what kind of instruction
    arg: Any = None                  # argument (e.g., REGEX pattern)


_Step = Tuple[int, Any, Optional[Action]]  # (opcode, arg, action)
_State = Tuple[int, int, int, int, int]  # (opidx, pos, mark, argidx, kwidx)
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
        if end < 0:
            return None
        else:
            return Match(s, pos, end, self.grammar[self.start], args, kwargs)

    def _match(self, s: str, pos: int, memo: Optional[Memo]):  # noqa: C901
        pi = self.pi
        stack: List[_State] = [
            (0, 0, -1, 0, 0),    # failure (top-level backtrack entry)
            (-1, -1, -1, 0, 0),  # success
        ]
        args: List[Any] = []
        kwargs: List[_Binding] = []

        idx = self._index[self.start]
        while stack:
            mark = -1
            opcode, arg = pi[idx]

            if opcode == REGEX:
                m = arg.match(s, pos)
                if m is None:
                    idx = FAILURE
                else:
                    pos = m.end()

            elif opcode == LITERAL:
                if s.startswith(arg, pos):
                    pos += len(arg)
                else:
                    idx = FAILURE

            # elif opcode == CLASS:
            #     # chars = arg
            #     try:
            #         if s[pos] in arg:
            #             end = pos + 1
            #             pos = end
            #         else:
            #             idx = FAILURE
            #     except IndexError:
            #         idx = FAILURE

            elif opcode == DOT:
                try:
                    s[pos]
                except IndexError:
                    idx = FAILURE
                else:
                    pos += 1

            elif opcode == BRANCH:
                stack.append(
                    (idx + arg, pos, mark, len(args), len(kwargs))
                )
                idx += 1
                continue

            elif opcode == CALL:
                stack.append((idx + 1, -1, -1, -1, -1))
                idx = self._index[arg]
                continue

            elif opcode == COMMIT:
                stack.pop()
                idx += arg
                continue

            elif opcode == UPDATE:
                next_idx, _, prev_mark, _, _ = stack.pop()
                stack.append(
                    (next_idx, pos, prev_mark, len(args), len(kwargs))
                )
                idx += arg
                continue

            elif opcode == RESTORE:
                pos = stack.pop()[1]
                idx += arg
                continue

            elif opcode == FAILTWICE:
                pos = stack.pop()[1]
                idx = FAILURE

            elif opcode == RETURN:
                idx = stack.pop()[0]
                continue

            elif opcode == APPLY:
                _, _, mark, argidx, kwidx = stack.pop()
                _args, _kwargs = arg(
                    s,
                    mark,
                    pos,
                    args[argidx:],
                    dict(kwargs[kwidx:])
                )
                args[argidx:] = _args
                if not _kwargs:
                    kwargs[kwidx:] = []
                else:
                    kwargs[kwidx:] = _kwargs.items()

            elif opcode == MARK:
                stack.append((-1, -1, pos, len(args), len(kwargs)))

            elif opcode == PASS:
                break

            elif opcode == FAIL:
                idx = FAILURE

            else:
                raise Error(f'invalid operation: {opcode}')

            if idx == FAILURE:
                idx, pos, markidx, argidx, kwidx = stack.pop()
                while pos < 0:  # pos is >= 0 only for backtracking entries
                    idx, pos, markidx, argidx, kwidx = stack.pop()
                args[argidx:] = []
                if kwargs:
                    kwargs[kwidx:] = []
            else:
                idx += 1

        if not stack:
            return -1, (), {}
        return pos, args, kwargs


def _make_program(grammar):
    """A "program" is a set of instructions and mappings."""
    index = {}
    pi = [Instruction(FAIL)]  # special instruction for general failure

    for name in grammar.definitions:
        index[name] = len(pi)
        _pi = _parsing_instructions(grammar[name])
        pi.extend(_pi)
        pi.append(Instruction(RETURN))

    pi.append(Instruction(PASS))  # success condition

    return pi, index


def _dot(defn):
    return [Instruction(DOT)]


def _lit(defn):
    return [Instruction(LITERAL, defn.args[0])]


def _cls(defn):
    s = (defn.args[0]
         .replace('[', '\\[')
         .replace(']', '\\]'))
    pat = re.compile(f'[{s}]')
    return [Instruction(REGEX, pat)]


def _rgx(defn):
    pat = re.compile(f'{defn.args[0]}', flags=defn.args[1])
    return [Instruction(REGEX, pat)]


def _opt(defn):
    pi = _parsing_instructions(defn.args[0])
    return [Instruction(BRANCH, len(pi) + 2),
            *pi,
            Instruction(COMMIT, 1)]


def _str(defn):
    pi = _parsing_instructions(defn.args[0])
    return [Instruction(BRANCH, len(pi) + 2),
            *pi,
            Instruction(UPDATE, -len(pi))]


def _pls(defn):
    pi = _parsing_instructions(defn.args[0])
    return [*pi,
            Instruction(BRANCH, len(pi) + 2),
            *pi,
            Instruction(UPDATE, -len(pi))]


def _sym(defn):
    return [Instruction(CALL, defn.args[0])]


def _and(defn):
    pi = _parsing_instructions(defn.args[0])
    return [Instruction(BRANCH, len(pi) + 2),
            *pi,
            Instruction(RESTORE, 2),
            Instruction(FAIL)]


def _not(defn):
    pi = _parsing_instructions(defn.args[0])
    return [Instruction(BRANCH, len(pi) + 2),
            *pi,
            Instruction(FAILTWICE)]


def _cap(defn):
    return _rul(Rule(defn.args[0], Capture(str)))


def _bnd(defn):
    return _rul(Rule(defn.args[0], Bind(defn.args[1])))


def _seq(defn):
    head = [pi
            for d in defn.args[0][:-1]
            for pi in _parsing_instructions(d)]
    tail = _parsing_instructions(defn.args[0][-1])
    return head + tail


def _chc(defn):
    # TODO: action
    pis = [_parsing_instructions(d) for d in defn.args[0]]
    pi = pis[-1]
    for _pi in reversed(pis[:-1]):
        pi = [Instruction(BRANCH, len(_pi) + 2),
              *_pi,
              Instruction(COMMIT, len(pi) + 1),
              *pi]
    return pi


def _rul(defn):
    subdefn, action, _ = defn.args
    pis = _parsing_instructions(subdefn)
    if action is None:
        return pis
    return [Instruction(MARK)] + pis + [Instruction(APPLY, action)]


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


def _parsing_instructions(defn):  # noqa: C901
    try:
        return _op_map[defn.op](defn)
    except KeyError:
        raise Error(f'invalid definition: {defn!r}')
