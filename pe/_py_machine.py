
"""
PEG Parsing Machine

Inspired by Medeiros and Ierusalimschy, 2008, "A Parsing Machine for PEGs"

"""

from typing import Union, Tuple, List, Dict, Optional, Any
from enum import IntEnum
import re

from pe._constants import FAIL as FAILURE, Operator, Flag
from pe._errors import Error
from pe._match import Match
from pe._types import Memo
from pe._definition import Definition
from pe._grammar import Grammar
from pe._parser import Parser
from pe._optimize import optimize
from pe._autoignore import autoignore
from pe.actions import Action, Bind
from pe.operators import Rule
from pe.patterns import DEFAULT_IGNORE


# Parser ###############################################################

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
    SCAN = 9
    NOOP = 10


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
SCAN = OpCode.SCAN
NOOP = OpCode.NOOP


class Scanner:
    def scan(self, s: str, pos: int = 0) -> int:
        try:
            return self._scan(s, pos, len(s))
        except IndexError:
            return FAILURE

    def _scan(self, s: str, pos: int, slen: int) -> int:
        return FAILURE


_State = Tuple[int, int, int, int, int]  # (opidx, pos, mark, argidx, kwidx)
_Binding = Tuple[str, Any]
_Instruction = Tuple[
    OpCode,
    int,                # index argument
    Optional[Scanner],  # scanner object or None
    bool,               # marking
    bool,               # capturing
    Optional[Action],   # rule action
    Optional[str]       # name
]
_Program = List[_Instruction]
_Index = Dict[str, int]


def Instruction(
    opcode: OpCode,
    oploc: int = 1,
    scanner: Optional[Scanner] = None,
    marking: bool = False,
    capturing: bool = False,
    action: Optional[Action] = None,
    name: Optional[str] = None,
) -> _Instruction:
    return (opcode, oploc, scanner, marking, capturing, action, name)


class MachineParser(Parser):

    def __init__(self, grammar: Grammar,
                 ignore: Optional[Definition] = DEFAULT_IGNORE,
                 flags: Flag = Flag.NONE):
        super().__init__(grammar, flags=flags)

        grammar = autoignore(grammar, ignore)

        grammar = optimize(grammar,
                           inline=flags & Flag.INLINE,
                           common=flags & Flag.COMMON,
                           regex=flags & Flag.REGEX)
        # if flags & Flag.DEBUG:
        #     grammar = debug(grammar)
        self.modified_grammar = grammar

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


def _match(  # noqa: C901
    pi: _Program,
    idx: int,
    s: str,
    pos: int,
    args: List[Any],
    kwargs: List[_Binding],
    memo: Optional[Memo],
) -> int:
    if s is None:
        raise TypeError
    if args is None:
        raise TypeError
    if kwargs is None:
        raise TypeError

    stack: List[_State] = [
        (0, 0, -1, 0, 0),    # failure (top-level backtrack entry)
        (-1, -1, -1, 0, 0),  # success
    ]

    # lookup optimizations
    push = stack.append
    pop = stack.pop
    slen = len(s)

    while stack:
        # print(idx, pos, s[pos], len(stack))
        # print(pi[idx])
        opcode, oploc, scanner, marking, capturing, action, name = pi[idx]

        if marking:
            push((0, -1, pos, len(args), len(kwargs)))

        if opcode == SCAN:
            assert scanner is not None
            pos = scanner._scan(s, pos, slen)
            if pos < 0:
                idx = FAILURE

        elif opcode == BRANCH:
            push((idx + oploc, pos, -1, len(args), len(kwargs)))
            idx += 1
            continue

        elif opcode == CALL:
            push((idx + 1, -1, -1, -1, -1))
            idx = oploc
            continue

        elif opcode == COMMIT:
            pop()
            idx += oploc
            continue

        elif opcode == UPDATE:
            next_idx, _, prev_mark, _, _ = pop()
            push((next_idx, pos, prev_mark, len(args), len(kwargs)))
            idx += oploc
            continue

        elif opcode == RESTORE:
            pos = pop()[1]
            idx += oploc
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


# Program Creation #####################################################

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
    pis = [(pi[0], index[pi[6]], *pi[2:]) if pi[0] == CALL else pi
           for pi in pis]
    pis.append(Instruction(PASS))  # success condition

    return pis, index


def _dot(defn):
    return [Instruction(SCAN, scanner=Dot())]


def _lit(defn):
    return [Instruction(SCAN, scanner=Literal(defn.args[0]))]


def _cls(defn, mincount=1, maxcount=1):
    cclass = CharacterClass(
        defn.args[0],
        negate=defn.args[1],
        mincount=mincount,
        maxcount=maxcount
    )
    return [Instruction(SCAN, scanner=cclass)]


def _rgx(defn):
    pat, flags = defn.args
    return [Instruction(SCAN, scanner=Regex(pat, flags=flags))]


def _opt(defn):
    pi = _parsing_instructions(defn.args[0])
    return [Instruction(BRANCH, len(pi) + 2),
            *pi,
            Instruction(COMMIT, 1)]


def _str(defn): return _rpt(defn, 0)


def _pls(defn): return _rpt(defn, 1)


def _rpt(defn, mincount):
    pis = _parsing_instructions(defn.args[0])
    if (
        len(pis) == 1
        and pis[0][0] == SCAN
        and isinstance(pis[0][2], CharacterClass)
        and not (pis[0][3] or pis[0][4])
        and pis[0][5] is None
    ):
        pi = pis[0]
        pi[2].mincount = mincount
        pi[2].maxcount = -1
        return [Instruction(SCAN,
                            scanner=pi[2],
                            marking=pi[3],
                            capturing=pi[4],
                            action=pi[5])]
    return [*(pis * mincount),
            Instruction(BRANCH, len(pis) + 2),
            *pis,
            Instruction(UPDATE, -len(pis))]


def _sym(defn):
    return [Instruction(CALL, name=defn.args[0])]


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
    captured_choice = defn.args[0].op == Operator.CHC
    pis = _parsing_instructions(defn.args[0])
    if not pis[0][3]:
        pis[0] = (*pis[0][:3], True, *pis[0][4:])
    else:
        pis.insert(0, Instruction(NOOP, marking=True))
    pi = pis[-1]
    if (not pi[4]  # not capturing
            and not pi[5]  # no action
            and pi[0] not in NO_CAP_OR_ACT
            and not captured_choice):
        pis[-1] = (*pi[:4], True, *pi[5:])
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
    if not pi[3]:
        pis[0] = (*pi[:3], True, *pi[4:])
    else:
        pis.insert(0, Instruction(NOOP, marking=True))
    pi = pis[-1]
    if not pi[5] and pi[0] not in NO_CAP_OR_ACT:
        pis[-1] = (*pi[:5], action, *pi[6:])
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
    op = defn.op
    if op in _op_map:
        return _op_map[defn.op](defn)
    else:
        raise Error(f'invalid definition: {defn!r}')


# Scanners #############################################################

class Dot(Scanner):
    def _scan(self, s: str, pos: int, slen: int) -> int:
        if pos < slen:
            return pos + 1
        return FAILURE


class Literal(Scanner):

    def __init__(self, x: str):
        self._x = x
        self._xlen = len(x)

    def _scan(self, s: str, pos: int, slen: int) -> int:
        end = pos + self._xlen
        if s[pos:end] != self._x:
            return FAILURE
        return end

    def __repr__(self):
        return f'{self.__class__.__name__}({self._x!r})'


class CharacterClass(Scanner):

    def __init__(
        self,
        ranges: List[Tuple[str, Union[str, None]]],
        negate: bool = False,
        mincount: int = 1,
        maxcount: int = 1
    ):
        self._chars = ''.join(a for a, b in ranges if not b)
        self._ranges = ''.join(a+b for a, b in ranges if b)
        self._rangelen = len(self._ranges)
        self._negate = negate
        self.mincount = mincount
        self.maxcount = maxcount

    def _scan(self, s: str, pos: int, slen: int) -> int:
        ranges = self._ranges
        rangelen = self._rangelen
        mincount = self.mincount
        maxcount = self.maxcount
        i = 0
        while maxcount and pos < slen:
            c = s[pos]
            matched = c in self._chars
            while i < rangelen:
                if ranges[i] <= c <= ranges[i+1]:
                    matched = True
                    break
                i += 2
            if matched ^ self._negate:
                pos += 1
                maxcount -= 1
                mincount -= 1
                i = 0
            else:
                break
        if mincount > 0:
            return FAILURE
        return pos

    def __repr__(self):
        clsstr = (self._chars
                  + ''.join(f'{a}-{b}'
                            for a, b in zip(self._ranges[::2],
                                            self._ranges[1::2])))
        return (f'{self.__class__.__name__}({clsstr!r},'
                f' negate={self._negate},'
                f' mincount={self.mincount},'
                f' maxcount={self.maxcount})')


class Regex(Scanner):
    def __init__(self, pattern: str, flags: int = 0):
        self._regex = re.compile(pattern, flags=flags)

    def _scan(self, s: str, pos: int, slen: int) -> int:
        m = self._regex.match(s, pos=pos)
        if m is None:
            return FAILURE
        else:
            return m.end()
