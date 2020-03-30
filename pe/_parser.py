
from typing import Union

from pe._constants import Flag
from pe._match import Match
from pe._definition import Definition
from pe._grammar import Grammar


class Parser:
    def __init__(self,
                 grammar: Union[Grammar, Definition],
                 flags: Flag = Flag.NONE):
        if isinstance(grammar, Definition):
            grammar = Grammar({'Start': grammar})
        self.grammar = grammar
        self.flags = flags

    def match(self, s: str, pos: int = 0, flags: Flag = Flag.NONE) -> Match:
        return NotImplemented
