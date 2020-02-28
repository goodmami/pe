
from pe.constants import NOMATCH, Operators as Op
from pe.core import Error
from pe.terms import (Dot, Literal, Class)
from pe.expressions import (
    Sequence,
    Choice,
    Repeat,
    Optional,
    And,
    Not,
    Grammar,
)


class State:
    __slots__ = 'pos', 'i', 'args', 'kwargs',
    def __init__(self, pos: int):
        self.pos: int = pos
        self.i: int = 0
        self.args: List = None
        self.kwargs: Dict = None


def match(grammar, s: str, pos: int = 0):
    memo = {}
    agenda = [((Op.DEF, grammar.start), State(pos))]
    index = 0
    slen = len(s)
    while agenda:
        agendum, state = agenda[index]
        op = agendum[0]
        # print(f'pos: {pos}\tindex: {index}\tstate.i: {state.i}\top: {op}')

        if index < 0:
            break

        if op == Op.RPT:
            i = state.i
            expr, min, max = agendum[1:]
            if pos == NOMATCH:  # item failed, ok if it matched enough
                if i >= min:
                    pos = agenda[index+1][1].pos  # use last successful pos
                index -= 1
            elif i == max:  # repeat finished
                index -= 1
            elif pos >= slen and i < min:  # end of string and not enough
                pos = NOMATCH
                index -= 1
            else:
                if i == 0:  # starting
                    agenda[index+1:] = [(expr, State(pos))]
                else:  # continuing; reset pos and state.i
                    next_state = agenda[index+1][1]
                    next_state.pos = pos
                    next_state.i = 0
                index += 1
                continue

        elif op == Op.DEF:
            if pos == NOMATCH:  # rule failed
                index -= 1
            else:
                name = agendum[1]
                if state.i:  # rule complete
                    # action = grammar.actions[name]
                    index -= 1
                    # do something
                else:  # entering rule
                    expr = grammar[name]
                    agenda[index+1:] = [(expr, State(pos))]
                    index += 1
                    continue

        elif op == Op.CHC:
            i = state.i
            exprs = agendum[1]
            # starting choice or choice item failed; reset pos and try next
            if i == 0 or (pos == NOMATCH and i < len(exprs)):
                pos = state.pos
                agenda[index+1:] = [(exprs[i], State(pos))]
                index += 1
                continue
            else:  # all choices failed or one succeeded
                index -= 1

        elif op == Op.SEQ:
            if pos == NOMATCH:  # sequence item failed
                index -= 1
            else:
                exprs = agendum[1]
                i = state.i
                if i >= len(exprs):  # sequence complete
                    index -= 1
                else:  # next sequence item
                    agenda[index+1:] = [(exprs[i], State(pos))]
                    index += 1
                    continue

        elif op == Op.LIT:
            string = agendum[1]
            if s.startswith(string, pos):
                pos += len(string)
            else:
                pos = NOMATCH
            index -= 1

        elif op == Op.CLS:
            chars = agendum[1]
            try:
                if s[pos] in chars:
                    pos += 1
                else:
                    pos = NOMATCH
            except IndexError:
                pos = NOMATCH
            index -= 1

        elif op == Op.DOT:
            try:
                s[pos]
            except IndexError:
                pos = NOMATCH
            else:
                pos = pos + 1
            index -= 1

        elif op == Op.AND:
            if state.i == 0:
                agenda[index+1:] = [(agendum[1], State(pos))]
                index += 1
                continue
            else:
                if pos != NOMATCH:
                    pos = state.pos
                index -= 1

        elif op == Op.NOT:
            if state.i == 0:
                agenda[index+1:] = [(agendum[1], State(pos))]
                index += 1
                continue
            else:
                if pos == NOMATCH:
                    pos = state.pos
                else:
                    pos = NOMATCH
                index -= 1

        else:
            raise Error(f'invalid operation: {op!r}')

        agenda[index][1].i += 1  # increment previous state's tally

    # print(f'done\tpos: {pos}')

class Grammar:
    def __init__(self):
        self.start = 'Start'
        self.rules = {}
        self.actions = {}
    def __getitem__(self, name):
        return self.rules[name]

g = Grammar()
g.rules['Start'] = (Op.SEQ, [(Op.LIT, '"'),
                             (Op.RPT, (Op.CHC, [
                                 (Op.SEQ, [(Op.LIT, '\\'), (Op.DOT,)]),
                                 (Op.SEQ, [(Op.NOT, (Op.LIT, '"')), (Op.DOT,)])]),
                              0, -1),
                             (Op.LIT, '"')])
