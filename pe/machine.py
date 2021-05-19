
"""
PEG Parsing Machine

Inspired by Medeiros and Ierusalimschy, 2008, "A Parsing Machine for PEGs"

"""

from typing import Union, Tuple, List, Dict, Optional, Any
import re
from enum import IntEnum

from pe._constants import FAIL as FAILURE, Operator, Flag
from pe._errors import Error
from pe._match import Match
from pe._types import Memo
from pe._grammar import Grammar
from pe._parser import Parser
from pe._escape import unescape
from pe._optimize import optimize
from pe.actions import Action, Bind
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
    REGEX = 9
    LITERAL = 10
    CLASS = 11
    DOT = 12
    NOOP = 13
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
REGEX = OpCode.REGEX
LITERAL = OpCode.LITERAL
CLASS = OpCode.CLASS
DOT = OpCode.DOT
NOOP = OpCode.NOOP


_State = Tuple[int, int, int, int, int]  # (opidx, pos, mark, argidx, kwidx)
_Binding = Tuple[str, Any]
_Instruction = Tuple[
    OpCode,
    Any,              # op argument
    bool,             # marking
    bool,             # capturing
    Optional[Action]  # rule action
]
_Program = List[_Instruction]
_Index = Dict[str, int]


def Instruction(
    opcode: OpCode,
    arg: Any = None,
    marking: bool = False,
    capturing: bool = False,
    action: Optional[Action] = None,
) -> _Instruction:
    return (opcode, arg, marking, capturing, action)


class MachineParser(Parser):

    def __init__(self, grammar: Grammar,
                 flags: Flag = Flag.NONE):
        super().__init__(grammar, flags=flags)

        grammar = optimize(grammar,
                           inline=flags & Flag.INLINE,
                           common=flags & Flag.COMMON,
                           regex=flags & Flag.REGEX)
        # if flags & Flag.DEBUG:
        #     grammar = debug(grammar)
        pi, index = _make_program(grammar)
        self.pi: _Program = pi
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
        args: List[Any] = []
        kwargs: List[_Binding] = []
        idx = self._index[self.start]
        end = _match(self.pi, idx, s, pos, args, kwargs, memo)
        if end < 0:
            return None
        else:
            return Match(
                s,
                pos,
                end,
                self.grammar[self.start],
                args,
                dict(kwargs)
            )


def _match(
    pi: _Program,
    idx: int,
    s: str,
    pos: int,
    args: List[Any],
    kwargs: List[_Binding],
    memo: Optional[Memo],
) -> int:
    stack: List[_State] = [
        (0, 0, -1, 0, 0),    # failure (top-level backtrack entry)
        (-1, -1, -1, 0, 0),  # success
    ]
    # lookup optimizations
    push = stack.append
    pop = stack.pop
    startswith = s.startswith

    while stack:
        mark = -1
        opcode, arg, marking, capturing, action = pi[idx]

        if marking:
            push((0, -1, pos, len(args), len(kwargs)))

        if opcode == REGEX:
            m = arg(s, pos)
            if m is None:
                idx = FAILURE
            else:
                pos = m.end()

        elif opcode == LITERAL:
            if startswith(arg, pos):
                pos += len(arg)
            else:
                idx = FAILURE

        elif opcode == CLASS:
            try:
                c = s[pos]
            except IndexError:
                idx = FAILURE
            else:
                i = 1
                matched = arg[0] == c
                max_i = len(arg) - 1
                while not matched and i < max_i:
                    if arg[i] == '-':
                        if arg[i-1] <= c <= arg[i+1]:
                            matched = True
                        i += 3
                    else:
                        if arg[i] == c:
                            matched = True
                        i += 1
                if not matched and arg[-1] == c:
                    matched = True
                if matched:
                    pos += 1
                else:
                    idx = FAILURE

        elif opcode == DOT:
            try:
                s[pos]
            except IndexError:
                idx = FAILURE
            else:
                pos += 1

        elif opcode == BRANCH:
            push((idx + arg, pos, mark, len(args), len(kwargs)))
            idx += 1
            continue

        elif opcode == CALL:
            push((idx + 1, -1, -1, -1, -1))
            idx = arg
            continue

        elif opcode == COMMIT:
            pop()
            idx += arg
            continue

        elif opcode == UPDATE:
            next_idx, _, prev_mark, _, _ = pop()
            push((next_idx, pos, prev_mark, len(args), len(kwargs)))
            idx += arg
            continue

        elif opcode == RESTORE:
            pos = pop()[1]
            idx += arg
            continue

        elif opcode == FAILTWICE:
            pos = pop()[1]
            idx = FAILURE

        elif opcode == RETURN:
            idx = pop()[0]
            continue

        elif opcode == PASS:
            break

        elif opcode == FAIL:
            idx = FAILURE

        elif opcode != NOOP:
            raise Error(f'invalid operation: {opcode}')

        if idx == FAILURE:
            idx, pos, _, argidx, kwidx = pop()
            while pos < 0:  # pos is >= 0 only for backtracking entries
                idx, pos, _, argidx, kwidx = pop()
            args[argidx:] = []
            if kwargs:
                kwargs[kwidx:] = []
        else:
            if capturing:
                _, _, mark, argidx, kwidx = pop()
                args[argidx:] = [s[mark:pos]]
                kwargs[kwidx:] = []

            if action:
                _, _, mark, argidx, kwidx = pop()
                _args, _kwargs = action(
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

            idx += 1

    if not stack:
        return -1
    return pos


# Captures and actions cannot be placed on these operators because of
# their effect on the stack
NO_CAP_OR_ACT = {CALL, COMMIT, UPDATE, RESTORE, FAILTWICE, RETURN}


def _make_program(grammar) -> Tuple[_Program, _Index]:
    """A "program" is a set of instructions and mappings."""
    index = {}
    pis: List[_Instruction] = []

    pis.append(Instruction(FAIL))  # special instruction for general failure
    for name in grammar.definitions:
        index[name] = len(pis)
        _pis = _parsing_instructions(grammar[name])
        pis.extend(_pis)
        pis.append(Instruction(RETURN))
    # replace call symbols with locations
    pis = [(pi[0], index[pi[1]], *pi[2:]) if pi[0] == CALL else pi
           for pi in pis]
    pis.append(Instruction(PASS))  # success condition

    return pis, index


def _dot(defn):
    return [Instruction(DOT)]


def _lit(defn):
    return [Instruction(LITERAL, defn.args[0])]


def _cls(defn):
    return [Instruction(CLASS, unescape(defn.args[0]))]


def _rgx(defn):
    pat = re.compile(f'{defn.args[0]}', flags=defn.args[1])
    return [Instruction(REGEX, pat.match)]


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
    pis = _parsing_instructions(defn.args[0])
    if not pis[0][2]:
        pis[0] = (*pis[0][:2], True, *pis[0][3:])
    else:
        pis.insert(0, Instruction(NOOP, marking=True))
    pi = pis[-1]
    if not pi[3] and not pi[4] and pi[0] not in NO_CAP_OR_ACT:
        pis[-1] = (*pi[:3], True, *pi[4:])
    else:
        pis.append(Instruction(NOOP, capturing=True))
    return pis


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
    pi = pis[0]
    if not pi[2]:
        pis[0] = (*pi[:2], True, *pi[3:])
    else:
        pis.insert(0, Instruction(NOOP, marking=True))
    pi = pis[-1]
    if not pi[4] and pi[0] not in NO_CAP_OR_ACT:
        pis[-1] = (*pi[:4], action)
    else:
        pis.append(Instruction(NOOP, action=action))
    return pis


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
