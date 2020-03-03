
from pe.constants import FAIL, Operator
from pe.core import Error, Grammar


class State:
    __slots__ = 'expr', 'pos', 'i',
    def __init__(self, expr, pos: int):
        self.expr = expr
        self.pos = pos
        self.i = 0


def match(grammar, s: str, pos: int = 0):
    DEF = Operator.DEF
    DOT = Operator.DOT
    LIT = Operator.LIT
    CLS = Operator.CLS
    SEQ = Operator.SEQ
    CHC = Operator.CHC
    RPT = Operator.RPT
    AND = Operator.AND
    NOT = Operator.NOT

    memo = {}
    agenda = [State((DEF, grammar.start), pos)]
    index = 0
    slen = len(s)
    while index >= 0:
        state = agenda[index]
        expr = state.expr
        op = expr[0]
        # print(f'pos: {pos}\tindex: {index}\tstate.i: {state.i}\top: {op}')

        if op == RPT:
            i = state.i
            subexpr, min, max = expr[1:]
            if pos == FAIL:  # item failed, ok if it matched enough
                if i >= min:
                    pos = agenda[index+1].pos  # use last successful pos
                index -= 1
            elif i == max:  # repeat finished
                index -= 1
            elif pos >= slen and i < min:  # end of string and not enough
                pos = FAIL
                index -= 1
            else:
                if i == 0:  # starting
                    agenda[index+1:] = [State(subexpr, pos)]
                else:  # continuing; reset pos and state.i
                    next_state = agenda[index+1]
                    next_state.pos = pos
                    next_state.i = 0
                index += 1
                continue

        elif op == DEF:
            if pos == FAIL:  # rule failed
                index -= 1
            else:
                name = expr[1]
                if state.i:  # rule complete
                    # action = grammar.actions[name]
                    index -= 1
                    # do something
                else:  # entering rule
                    subexpr = grammar[name]
                    agenda[index+1:] = [State(subexpr, pos)]
                    index += 1
                    continue

        elif op == CHC:
            i = state.i
            subexprs = expr[1]
            # starting choice or choice item failed; reset pos and try next
            if i == 0 or (pos == FAIL and i < len(subexprs)):
                pos = state.pos
                agenda[index+1:] = [State(subexprs[i], pos)]
                index += 1
                continue
            else:  # all choices failed or one succeeded
                index -= 1

        elif op == SEQ:
            if pos == FAIL:  # sequence item failed
                index -= 1
            else:
                subexprs = expr[1]
                i = state.i
                if i >= len(subexprs):  # sequence complete
                    index -= 1
                else:  # next sequence item
                    agenda[index+1:] = [State(subexprs[i], pos)]
                    index += 1
                    continue

        elif op == LIT:
            string = expr[1]
            l = len(string)
            if s[pos:pos+l] == string:
                pos += l
            else:
                pos = FAIL
            index -= 1

        elif op == CLS:
            chars = expr[1]
            try:
                if s[pos] in chars:
                    pos += 1
                else:
                    pos = FAIL
            except IndexError:
                pos = FAIL
            index -= 1

        elif op == DOT:
            try:
                s[pos]
            except IndexError:
                pos = FAIL
            else:
                pos = pos + 1
            index -= 1

        elif op == AND:
            if state.i == 0:
                agenda[index+1:] = [State(expr[1], pos)]
                index += 1
                continue
            else:
                if pos != FAIL:
                    pos = state.pos
                index -= 1

        elif op == NOT:
            if state.i == 0:
                agenda[index+1:] = [State(expr[1], pos)]
                index += 1
                continue
            else:
                if pos == FAIL:
                    pos = state.pos
                else:
                    pos = FAIL
                index -= 1

        else:
            raise Error(f'invalid operation: {op!r}')

        agenda[index].i += 1  # increment previous state's tally

    # print(f'done\tpos: {pos}')

g = Grammar()
g.rules['Start'] = (
    Operator.SEQ, [
        (Operator.LIT, '"'),
        (Operator.RPT, (Operator.CHC, [
            (Operator.SEQ, [(Operator.LIT, '\\'), (Operator.DOT,)]),
            (Operator.SEQ, [
                (Operator.NOT, (Operator.LIT, '"')), (Operator.DOT,)])]),
         0, -1),
        (Operator.LIT, '"')])
