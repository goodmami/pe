
"""
PEG Parsing Machine

Inspired by Medeiros and Ierusalimschy, 2008, "A Parsing Machine for PEGs"

"""

from typing import Union, Tuple, List, Dict, Optional, Any
import re
from enum import IntEnum

from cpython.mem cimport PyMem_Malloc, PyMem_Free

from pe._constants import Operator, Flag
from pe._errors import Error
from pe._match import Match
from pe._types import Memo
from pe._grammar import Grammar
from pe._parser import Parser
from pe._escape import unescape
from pe._optimize import optimize
from pe.actions import Action, Bind
from pe.operators import Rule


DEF FAILURE = -1

cdef enum OpCode:
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
    TERMINAL = 9
    NOOP = 10


cdef struct State:
    int opidx
    int pos
    int mark
    int argidx
    int kwidx
    State* prev


cdef State* push(
    int opidx,
    int pos,
    int mark,
    int argidx,
    int kwidx,
    State* prev
) except NULL:
    cdef State* state = <State*>PyMem_Malloc(sizeof(State))
    if not state:
        raise MemoryError()
    state.opidx = opidx
    state.pos = pos
    state.mark = mark
    state.argidx = argidx
    state.kwidx = kwidx
    state.prev = prev
    return state


cdef State* pop(State* state) except? NULL:
    if not state:
        raise Error('pop from empty stack')
    cdef State* prev = state.prev
    PyMem_Free(state)
    return prev


_Binding = Tuple[str, Any]
_Instruction = Tuple[
    int,              # OpCode,
    Any,              # op argument
    bool,             # marking
    bool,             # capturing
    Optional[Action]  # rule action
]
_Program = List[_Instruction]
_Index = Dict[str, int]


def Instruction(
    opcode: int, #OpCode,
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
                           regex=False)
        # if flags & Flag.DEBUG:
        #     grammar = debug(grammar)
        pi, index = _make_program(grammar)
        self._parser = _Parser(pi)
        self._index = index

    @property
    def start(self):
        return self.grammar.start

    def __contains__(self, name: str) -> bool:
        return name in self._index

    def match(self,
              str s,
              int pos = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        memo: Union[Memo, None] = None
        args: List[Any] = []
        kwargs: List[_Binding] = []
        idx = self._index[self.start]
        end = self._parser.match(idx, s, pos, args, kwargs, memo)
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


cdef class _Parser:
    cdef list pi

    def __init__(self, list pi):
        self.pi = pi

    cpdef int match(
        self,
        int idx,
        str s,
        int pos,
        list args,
        list kwargs,
        dict memo,
    ) except -2:
        cdef State* state
        cdef int retval = -1
        state = push(0, 0, -1, 0, 0, NULL)     # failure (top backtrack entry)
        state = push(-1, -1, -1, 0, 0, state)  # success
        try:
            state = self._match(idx, s, pos, args, kwargs, memo, state)
            retval = state.pos
        finally:
            while state:
                state = pop(state)
        return retval

    cdef State* _match(
        self,
        int idx,
        str s,
        int pos,
        list args,
        list kwargs,
        dict memo,
        State* state,
    ) except NULL:
        if s is None:
            raise TypeError
        if args is None:
            raise TypeError
        if kwargs is None:
            raise TypeError
        # lookup optimizations
        pi = self.pi
        cdef OpCode opcode
        cdef int slen = len(s)
        cdef Scanner scanner
        while state:
            opcode, arg, marking, capturing, action = pi[idx]

            if marking:
                state = push(0, -1, pos, len(args), len(kwargs), state)

            if opcode == TERMINAL:
                scanner = arg
                pos = scanner._scan(s, pos, slen)
                if pos < 0:
                    idx = FAILURE

            elif opcode == BRANCH:
                state = push(idx + arg, pos, -1, len(args), len(kwargs), state)
                idx += 1
                continue

            elif opcode == CALL:
                state = push(idx + 1, -1, -1, -1, -1, state)
                idx = arg
                continue

            elif opcode == COMMIT:
                state = pop(state)
                idx += arg
                continue

            elif opcode == UPDATE:
                state.pos = pos
                state.argidx = len(args)
                state.kwidx = len(kwargs)
                idx += arg
                continue

            elif opcode == RESTORE:
                pos = state.pos
                state = pop(state)
                idx += arg
                continue

            elif opcode == FAILTWICE:
                pos = state.pos
                state = pop(state)
                idx = FAILURE

            elif opcode == RETURN:
                idx = state.opidx
                state = pop(state)
                continue

            elif opcode == PASS:
                break

            elif opcode == FAIL:
                idx = FAILURE

            elif opcode != NOOP:
                raise Error(f'invalid operation: {opcode}')

            if idx == FAILURE:
                # pos is >= 0 only for backtracking entries
                while state and state.pos < 0:
                    state = pop(state)
                idx = state.opidx
                pos = state.pos
                args[state.argidx:] = []
                if kwargs:
                    kwargs[state.kwidx:] = []
                state = pop(state)  # pop backtracking entry
            else:
                if capturing:
                    args[state.argidx:] = [s[state.mark:pos]]
                    kwargs[state.kwidx:] = []
                    state = pop(state)

                if action:
                    _args, _kwargs = action(
                        s,
                        state.mark,
                        pos,
                        args[state.argidx:],
                        dict(kwargs[state.kwidx:])
                    )
                    args[state.argidx:] = _args
                    if not _kwargs:
                        kwargs[state.kwidx:] = []
                    else:
                        kwargs[state.kwidx:] = _kwargs.items()
                    state = pop(state)

                idx += 1

        if not state:
            state = push(0, -1, -1, 0, 0, NULL)
        else:
            state.pos = pos
        return state


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
    return [Instruction(TERMINAL, Dot())]


def _lit(defn):
    return [Instruction(TERMINAL, Literal(defn.args[0]))]


def _cls(defn, mincount=1, maxcount=1):
    return [Instruction(TERMINAL,
                        CharacterClass(unescape(defn.args[0]),
                                       negate=defn.args[1],
                                       mincount=mincount,
                                       maxcount=maxcount))]


def _rgx(defn):
    pat = re.compile(f'{defn.args[0]}', flags=defn.args[1])
    return [Instruction(TERMINAL, Regex(pat))]


def _opt(defn):
    pi = _parsing_instructions(defn.args[0])
    return [Instruction(BRANCH, len(pi) + 2),
            *pi,
            Instruction(COMMIT, 1)]


def _str(defn): return _rpt(defn, 0)
def _pls(defn): return _rpt(defn, 1)


def _rpt(defn, mincount):
    pi = _parsing_instructions(defn.args[0])
    if (len(pi) == 1
        and pi[0][0] == TERMINAL
        and isinstance(pi[0][1], CharacterClass)
        and not any(x for x in pi[0][2:])
    ):
        _, scanner, marking, capturing, action = pi[0]
        scanner.mincount = mincount
        scanner.maxcount = -1
        return [Instruction(TERMINAL,
                            scanner,
                            marking=marking,
                            capturing=capturing,
                            action=action)]
    return [*(pi * mincount),
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


cdef class Scanner:
    cpdef int scan(self, str s, int pos=0) except -2:
        try:
            return self._scan(s, pos, len(s))
        except IndexError:
            return FAILURE

    cdef int _scan(self, str s, int pos, int slen) except -2:
        return FAILURE


cdef class Dot(Scanner):
    cdef int _scan(self, str s, int pos, int slen) except -2:
        if pos < slen:
            return pos + 1
        return FAILURE


cdef class Literal(Scanner):
    cdef str _x
    cdef int _xlen

    def __init__(self, str x):
        self._x = x
        self._xlen = len(x)

    cdef int _scan(self, str s, int pos, int slen) except -2:
        cdef int end = pos + self._xlen
        if s[pos:end] != self._x:
            return FAILURE
        return end


cdef class CharacterClass(Scanner):
    cdef list _ranges
    cdef str _chars
    cdef bint _negate
    cdef public:
        int mincount, maxcount

    def __init__(
        self,
        str clsstr,
        bint negate = False,
        int mincount = 1,
        int maxcount = 1
    ):
        cdef list ranges = [], chars = []
        cdef int i = 0, n = len(clsstr)
        while i < n-2:
            if clsstr[i+1] == '-':
                ranges.append((clsstr[i], clsstr[i+2]))
                i += 3
            else:
                chars.append(clsstr[i])
                i += 1
        # remaining character(s) cannot be ranges
        while i < n:
            chars.append(clsstr[i])
            i += 1
        self._chars = ''.join(chars)
        self._ranges = ranges
        self._negate = negate
        self.mincount = mincount
        self.maxcount = maxcount

    cdef int _scan(self, str s, int pos, int slen) except -2:
        cdef Py_UCS4 a, b, c
        cdef bint matched
        cdef int mincount = self.mincount
        cdef int maxcount = self.maxcount
        while maxcount and pos < slen:
            c = s[pos]
            matched = False
            if c in self._chars:
                matched = True
            else:
                for a, b in self._ranges:
                    if a <= c <= b:
                        matched = True
                        break
            if matched ^ self._negate:
                pos += 1
                maxcount -= 1
                mincount -= 1
            else:
                break
        if mincount > 0:
            return FAILURE
        return pos


cdef class Regex(Scanner):
    cdef object _regex

    def __init__(self, object pattern):
        if hasattr(pattern, 'match'):
            self._regex = pattern
        else:
            self._regex = re.compile(pattern)

    cdef int _scan(self, str s, int pos, int slen) except -2:
        m = self._regex.match(s, pos=pos)
        if m is None:
            return FAILURE
        else:
            return m.end()
