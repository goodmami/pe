
from collections import defaultdict
import re

from pe.constants import FAIL, Operator
from pe.core import Error, Grammar


class State:
    __slots__ = 'expr', 'pos', 'i',
    def __init__(self, expr, pos: int):
        self.expr = expr
        self.pos = pos
        self.i = 0


def match(grammar, s: str, pos: int = 0):
    DOT = Operator.DOT
    LIT = Operator.LIT
    CLS = Operator.CLS
    RGX = Operator.RGX
    SYM = Operator.SYM
    OPT = Operator.OPT
    RPT = Operator.RPT
    AND = Operator.AND
    NOT = Operator.NOT
    DIS = Operator.DIS
    BND = Operator.BND
    SEQ = Operator.SEQ
    CHC = Operator.CHC
    RUL = Operator.RUL

    memo = defaultdict(dict)
    agenda = [State(grammar[grammar.start], pos)]
    index = 0
    slen = len(s)
    while index >= 0:
        state = agenda[index]
        expr = state.expr

        op = expr.op
        args = expr.args
        push = False
        # print(f'pos: {pos}\tindex: {index}\tstate.i: {state.i}\top: {op}')

        if op == RPT:
            i = state.i
            subexpr, min, max = expr.args
            if pos == FAIL:  # item failed, ok if it matched enough
                if i >= min:
                    pos = agenda[index+1].pos  # use last successful pos
            elif i == max:  # repeat finished
                pass
            elif pos >= slen and i < min:  # end of string and not enough
                pos = FAIL
            else:
                if i == 0:  # starting
                    agenda[index+1:] = [State(subexpr, pos)]
                else:  # continuing; reset pos and state.i
                    next_state = agenda[index+1]
                    next_state.pos = pos
                    next_state.i = 0
                push = True

        elif op == SYM:
            # memoization
            # _id = id(expr)
            if pos < 0:
                pass
            # elif _id in memo[pos]:
            #     pos, push = memo[pos][_id]
            else:
                name = args[0]
                if state.i:  # rule complete
                    # action = grammar.actions[name]
                    # do something
                    pass
                else:  # entering rule
                    subexpr = grammar[name]
                    agenda[index+1:] = [State(subexpr, pos)]
                    push = True

                # memo[pos][_id] = (pos, push)

        elif op == CHC:
            i = state.i
            subexprs = args[0]
            # starting choice or choice item failed; reset pos and try next
            if i == 0 or (pos == FAIL and i < len(subexprs)):
                pos = state.pos
                agenda[index+1:] = [State(subexprs[i], pos)]
                push = True
            else:  # all choices failed or one succeeded
                pass

        elif op == SEQ:
            if pos < 0:
                pass
            else:
                subexprs = args[0]
                i = state.i
                if i >= len(subexprs):  # sequence complete
                    pass
                else:  # next sequence item
                    agenda[index+1:] = [State(subexprs[i], pos)]
                    push = True

        elif op == RGX:
            pattern = re.compile(args[0])
            # pattern = args[0]
            m = pattern.match(s, pos)
            if m is None:
                pos = FAIL
            else:
                pos = m.end()

        elif op == LIT:
            string = args[0]
            l = len(string)
            if s[pos:pos+l] == string:
                pos += l
            else:
                pos = FAIL

        elif op == CLS:
            chars = args[0]
            try:
                if s[pos] in chars:
                    pos += 1
                else:
                    pos = FAIL
            except IndexError:
                pos = FAIL

        elif op == DOT:
            try:
                s[pos]
            except IndexError:
                pos = FAIL
            else:
                pos = pos + 1

        elif op == OPT:
            if state.i == 0:
                agenda[index+1:] = [State(args[0], pos)]
                push = True
            else:
                if pos == FAIL:
                    pos = state.pos

        elif op == AND:
            if state.i == 0:
                agenda[index+1:] = [State(args[0], pos)]
                push = True
            else:
                if pos != FAIL:
                    pos = state.pos

        elif op == NOT:
            if state.i == 0:
                agenda[index+1:] = [State(args[0], pos)]
                push = True
            else:
                if pos == FAIL:
                    pos = state.pos
                else:
                    pos = FAIL

        elif op == BND:
            if state.i == 0:
                agenda[index+1:] = [State(args[1], pos)]
                push = True
            else:
                if pos == FAIL:
                    pos = state.pos
                else:
                    pos = FAIL

        elif op == DIS:
            if state.i == 0:
                agenda[index+1:] = [State(args[0], pos)]
                push = True

        elif op == RUL:
            if pos < 0 or state.i:  # rule complete
                # action = grammar.actions[name]
                # do something
                pass
            else:  # entering rule
                subexpr = args[0]
                agenda[index+1:] = [State(subexpr, pos)]
                push = True

        else:
            raise Error(f'invalid operation: {op!r}')

        if push:
            index += 1
        else:
            index -= 1
            agenda[index].i += 1  # increment previous state's tally

    # print(f'done\tpos: {pos}')

g = Grammar()
g.definitions['Start'] = (
    Operator.SEQ, [
        (Operator.LIT, '"'),
        (Operator.RPT, (Operator.CHC, [
            (Operator.SEQ, [(Operator.LIT, '\\'), (Operator.DOT,)]),
            (Operator.SEQ, [
                (Operator.NOT, (Operator.LIT, '"')), (Operator.DOT,)])]),
         0, -1),
        (Operator.LIT, '"')])
