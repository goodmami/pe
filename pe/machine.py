
import sys

from typing import Type
from pe._parser import Parser
from pe import _py_machine
try:
    from pe import _cy_machine
except ImportError:
    _cy_machine = None  # type: ignore

__all__ = ['MachineParser']


MachineParser: Type[Parser]

# only use the extension module if it's available and we're in CPython
if _cy_machine is None or sys.implementation.name != 'cpython':
    MachineParser = _py_machine.MachineParser
else:
    MachineParser = _cy_machine.MachineParser
