
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
from pe._optimize import optimize
from pe.actions import Action, Bind
from pe.operators import Rule


DEF FAILURE = -1


# Parser ###############################################################

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
    SCAN = 9
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
_Index = Dict[str, int]


cdef class Scanner:
    cpdef int scan(self, str s, int pos=0) except -2:
        try:
            return self._scan(s, pos, len(s))
        except IndexError:
            return FAILURE

    cdef int _scan(self, str s, int pos, int slen) except -2:
        return FAILURE


cdef class Instruction:
    cdef public:
        OpCode opcode
        short oploc
        Scanner scanner
        bint marking
        bint capturing
        object action
        str name

    def __init__(
        self,
        OpCode opcode,
        short oploc=1,
        Scanner scanner=None,
        bint marking=False,
        bint capturing=False,
        object action=None,
        str name=None
    ):
        self.opcode = opcode
        self.oploc = oploc
        self.scanner = scanner
        self.marking = marking
        self.capturing = capturing
        self.action = action
        self.name = name


_Program = List[Instruction]


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
        # cdef OpCode opcode
        cdef int slen = len(s)
        cdef Instruction instr
        while state:
            instr = pi[idx]

            if instr.marking:
                state = push(0, -1, pos, len(args), len(kwargs), state)

            if instr.opcode == SCAN:
                pos = instr.scanner._scan(s, pos, slen)
                if pos < 0:
                    idx = FAILURE

            elif instr.opcode == BRANCH:
                state = push(idx + instr.oploc, pos, -1, len(args), len(kwargs), state)
                idx += 1
                continue

            elif instr.opcode == CALL:
                state = push(idx + 1, -1, -1, -1, -1, state)
                idx = instr.oploc
                continue

            elif instr.opcode == COMMIT:
                state = pop(state)
                idx += instr.oploc
                continue

            elif instr.opcode == UPDATE:
                state.pos = pos
                state.argidx = len(args)
                state.kwidx = len(kwargs)
                idx += instr.oploc
                continue

            elif instr.opcode == RESTORE:
                pos = state.pos
                state = pop(state)
                idx += instr.oploc
                continue

            elif instr.opcode == FAILTWICE:
                pos = state.pos
                state = pop(state)
                idx = FAILURE

            elif instr.opcode == RETURN:
                idx = state.opidx
                state = pop(state)
                continue

            elif instr.opcode == PASS:
                break

            elif instr.opcode == FAIL:
                idx = FAILURE

            elif instr.opcode != NOOP:
                raise Error(f'invalid operation: {instr.opcode}')

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
                if instr.capturing:
                    args[state.argidx:] = [s[state.mark:pos]]
                    kwargs[state.kwidx:] = []
                    state = pop(state)

                if instr.action is not None:
                    _args, _kwargs = instr.action(
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


# Program Creation #####################################################

# Captures and actions cannot be placed on these operators because of
# their effect on the stack
NO_CAP_OR_ACT = {CALL, COMMIT, UPDATE, RESTORE, FAILTWICE, RETURN}


def _make_program(grammar) -> Tuple[_Program, _Index]:
    """A "program" is a set of instructions and mappings."""
    index = {}
    pis: _Program = []

    pis.append(Instruction(FAIL))  # special instruction for general failure
    for name in grammar.definitions:
        index[name] = len(pis)
        _pis = _parsing_instructions(grammar[name])
        pis.extend(_pis)
        pis.append(Instruction(RETURN))

    # add locations to calls
    for pi in pis:
        if pi.opcode == CALL:
            pi.oploc = index[pi.name]

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
    if (len(pis) == 1
        and pis[0].opcode == SCAN
        and isinstance(pis[0].scanner, CharacterClass)
        and not (pis[0].marking or pis[0].capturing)
        and pis[0].action is None
    ):
        pi = pis[0]
        pi.scanner.mincount = mincount
        pi.scanner.maxcount = -1
        return [Instruction(SCAN,
                            scanner=pi.scanner,
                            marking=pi.marking,
                            capturing=pi.capturing,
                            action=pi.action)]
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
    if not pis[0].marking:
        pis[0].marking = True
    else:
        pis.insert(0, Instruction(NOOP, marking=True))
    pi = pis[-1]
    if (not pi.capturing
        and pi.action is None
        and pi.opcode not in NO_CAP_OR_ACT
        and not captured_choice
    ):
        pis[-1].capturing = True
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
    if not pi.marking:
        pi.marking = True
    else:
        pis.insert(0, Instruction(NOOP, marking=True))
    pi = pis[-1]
    if pi.action is None and pi.opcode not in NO_CAP_OR_ACT:
        pi.action = action
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


# Scanners #############################################################

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
    cdef:
        str _chars, _ranges
        int _rangelen
        bint _negate
    cdef public:
        int mincount, maxcount

    def __init__(
        self,
        list ranges,
        bint negate = False,
        int mincount = 1,
        int maxcount = 1
    ):
        self._chars = ''.join(a for a, b in ranges if not b)
        self._ranges = ''.join(a+b for a, b in ranges if b)
        self._rangelen = len(self._ranges)
        self._negate = negate
        self.mincount = mincount
        self.maxcount = maxcount

    cdef int _scan(self, str s, int pos, int slen) except -2:
        cdef Py_UCS4 c
        cdef str ranges = self._ranges
        cdef bint matched
        cdef int mincount = self.mincount
        cdef int maxcount = self.maxcount
        cdef int i = 0
        while maxcount and pos < slen:
            c = s[pos]
            matched = False
            if c in self._chars:
                matched = True
            else:
                while i < self._rangelen:
                    if ranges[i] <= c <= ranges[i+1]:
                        matched = True
                        break
                    i += 2
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

    def __init__(self, str pattern, int flags=0):
        self._regex = re.compile(pattern, flags=flags)

    cdef int _scan(self, str s, int pos, int slen) except -2:
        m = self._regex.match(s, pos=pos)
        if m is None:
            return FAILURE
        else:
            return m.end()


# Debugging ############################################################

# _OpCodeNames = {
#     FAIL: 'FAIL',
#     PASS: 'PASS',
#     BRANCH: 'BRANCH',
#     COMMIT: 'COMMIT',
#     UPDATE: 'UPDATE',
#     RESTORE: 'RESTORE',
#     FAILTWICE: 'FAILTWICE',
#     CALL: 'CALL',
#     RETURN: 'RETURN',
#     JUMP: 'JUMP',
#     SCAN: 'SCAN',
#     NOOP: 'NOOP',
# }


# cdef _print_program(pis: _Program):
#     for i, pi in enumerate(pis):
#         print(i,
#               _OpCodeNames[pi.opcode],
#               f'{pi.oploc:+}',
#               'marking' if pi.marking else '',
#               'capturing' if pi.capturing else '',
#               'name' if pi.name else '')


# cdef _print_stack(State* state):
#     states = []
#     while state:
#         states.append(
#             f'<State (opidx={state.opidx}, pos={state.pos}, mark={state.mark},'
#             f' argidx={state.argidx}, kwidx={state.kwidx})>'
#         )
#         state = state.prev
#     print(f'stack ({len(states)} entries):')
#     for i, s in enumerate(reversed(states)):
#         print(' '*i, s)
