
"""
PEG Parsing Machine

Inspired by Medeiros and Ierusalimschy, 2008, "A Parsing Machine for PEGs"

"""

from typing import Union, Tuple, List
import enum
from collections import defaultdict
import re

from pe._constants import FAIL, Operator, Flag
from pe._core import Error, Grammar, Definition, Expression, Match


class MachineOp(enum.Flag):
    PASS = enum.auto()
    BRANCH = enum.auto()  # aka Choice
    COMMIT = enum.auto()
    UPDATE = enum.auto()  # aka PartialCommit
    RESTORE = enum.auto() # aka BackCommit
    FAILTWICE = enum.auto()
    CALL = enum.auto()
    RETURN = enum.auto()
    JUMP = enum.auto()


class MachineParser(Expression):
    __slots__ = 'grammar', 'pi', '_index',

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        pi, index = _make_program(grammar)
        self.pi = pi
        self._index = index

    @property
    def start(self):
        return self.grammar.start

    # def __getitem__(self, name: str) -> Expression:
    #     return self._index[name]

    def __contains__(self, name: str) -> bool:
        return name in self._index

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        PASS      = MachineOp.PASS
        BRANCH    = MachineOp.BRANCH
        COMMIT    = MachineOp.COMMIT
        UPDATE    = MachineOp.UPDATE
        RESTORE   = MachineOp.RESTORE
        FAILTWICE = MachineOp.FAILTWICE
        CALL      = MachineOp.CALL
        RETURN    = MachineOp.RETURN
        JUMP      = MachineOp.JUMP
        RGX = Operator.RGX
        LIT = Operator.LIT
        CLS = Operator.CLS
        DOT = Operator.DOT
        DIS = Operator.DIS
        BND = Operator.BND
        RUL = Operator.RUL

        pi = self.pi
        stack = [(0, 0),
                 (-1, -1)]
        fails = []
        idx = self._index[self.start]
        i = pos
        while True:
            step = pi[idx]
            op = step[0]
            # print(f'idx: {idx}\ti: {i}\tstep: {step}')
            # print(stack)
            if op == RGX:
                m = step[1].match(s, i)
                if m is None:
                    idx = FAIL
                else:
                    i = m.end()

            elif op == LIT:
                string = step[1]
                sl = len(string)
                if s[i:i+sl] == string:
                    i += sl
                else:
                    idx = FAIL

            elif op == CLS:
                chars = step[1]
                try:
                    if s[i] in chars:
                        i += 1
                    else:
                        idx = FAIL
                except IndexError:
                    idx = FAIL

            elif op == DOT:
                try:
                    s[i]
                except IndexError:
                    idx = FAIL
                else:
                    i += 1

            elif op == BRANCH:
                offset = step[1]
                stack.append((idx + offset, i))
                idx += 1
                continue

            elif op == CALL:
                name = step[1]
                stack.append((idx + 1, -1))
                idx = self._index[name]
                continue

            elif op == COMMIT:
                offset = step[1]
                stack.pop()
                idx += offset
                continue

            elif op == UPDATE:
                offset = step[1]
                next_idx, _ = stack.pop()
                stack.append((next_idx, i))
                idx += offset
                continue

            elif op == RESTORE:
                offset = step[1]
                _, i = stack.pop()
                idx += offset
                continue

            elif op == FAILTWICE:
                _, i = stack.pop()
                idx = -1

            elif op == RETURN:
                idx, _ = stack.pop()
                continue

            elif op in (DIS, BND, RUL):
                pass

            elif op == PASS:
                break
            elif op == FAIL:
                idx = FAIL
            else:
                raise Error(f'invalid operation: {op}')

            if idx == FAIL:
                n = _n_to_backtrack(stack)
                # fails = stack[n:] + [(idx, i)]
                idx, i = stack[n]
                stack[n:] = []
            else:
                idx += 1

        return i


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
    pi = [(FAIL,)]  # special instruction for general failure

    for name in grammar.definitions:
        index[name] = len(pi)
        _pi = _parsing_instructions(grammar[name])
        pi.extend(_pi)
        pi.append((MachineOp.RETURN,))

    pi.append((MachineOp.PASS,))  # success condition

    return pi, index


def _parsing_instructions(defn):
    op = defn.op
    args = defn.args

    if op == Operator.DOT:
        return [(op,)]
    elif op == Operator.LIT:
        return [(op, args[0])]
    elif op == Operator.CLS:
        return [(Operator.RGX, re.compile(f'[{args[0]}]'))]
        # return [(op, args[0])]  # TODO: validate ranges
    elif op == Operator.RGX:
        return [(op, re.compile(args[0], flags=args[1]))]

    elif op == Operator.OPT:
        pi = _parsing_instructions(args[0])
        return [(MachineOp.BRANCH, len(pi) + 2),
                *pi,
                (MachineOp.COMMIT, 1)]

    elif op == Operator.STR:
        pi = _parsing_instructions(args[0])
        return [(MachineOp.BRANCH, len(pi) + 2),
                *pi,
                (MachineOp.UPDATE, -len(pi))]

    elif op == Operator.PLS:
        pi = _parsing_instructions(args[0])
        return [*pi,
                (MachineOp.BRANCH, len(pi) + 2),
                *pi,
                (MachineOp.UPDATE, -len(pi))]

    elif op == Operator.SYM:
        return [(MachineOp.CALL, args[0])]

    elif op == Operator.AND:
        pi = _parsing_instructions(args[0])
        return [(MachineOp.BRANCH, len(pi) + 2),
                *pi,
                (MachineOp.RESTORE, 2),
                (FAIL,)]

    elif op == Operator.NOT:
        pi = _parsing_instructions(args[0])
        return [(MachineOp.BRANCH, len(pi) + 2),
                *pi,
                (MachineOp.FAILTWICE,)]

    elif op == Operator.RAW:
        pi = _parsing_instructions(args[0])
        return pi  # TODO: raw

    elif op == Operator.DIS:
        return _parsing_instructions(args[0])
        # return [(op,)] + pi
    elif op == Operator.BND:
        return _parsing_instructions(args[0])
        # return [(op, args[0])] + pi

    elif op == Operator.SEQ:
        return [pi
                for d in args[0]
                for pi in _parsing_instructions(d)]

    elif op == Operator.CHC:
        pis = [_parsing_instructions(d) for d in args[0]]
        pi = pis[-1]
        for _pi in reversed(pis[:-1]):
            pi = [(MachineOp.BRANCH, len(_pi) + 2),
                  *_pi,
                  (MachineOp.COMMIT, len(pi) + 1),
                  *pi]
        return pi

    elif op == Operator.RUL:
        return _parsing_instructions(args[0])
        # return [(op, args[1]),
        #         *_parsing_instructions(args[0])]

    else:
        raise Error(f'invalid definition: {_def!r}')
