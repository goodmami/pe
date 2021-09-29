
try:
    from pe._cy_machine import MachineParser
except ImportError:
    from pe._py_machine import MachineParser  # type: ignore


__all__ = ['MachineParser']
