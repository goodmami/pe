
from typing import Union, Optional

from pe._constants import Flag
from pe._match import Match
from pe._definition import Definition
from pe._grammar import Grammar


class Parser:
    grammar: Grammar
    modified_grammar: Grammar
    flags: Flag

    def __init__(self,
                 grammar: Union[Grammar, Definition],
                 ignore: Optional[Definition] = None,
                 flags: Flag = Flag.NONE):
        if isinstance(grammar, Definition):
            grammar = Grammar({'Start': grammar})
        self.grammar = grammar
        self.modified_grammar = grammar  # may be reassigned later
        self.flags = flags

    def match(self,
              s: str,
              pos: int = 0,
              flags: Flag = Flag.NONE) -> Union[Match, None]:
        return NotImplemented
