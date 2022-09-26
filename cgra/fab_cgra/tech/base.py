from amaranth import *
from ..core.util import *

__all__ = ["BaseTech"]

class BaseTech:
    def __init__(self):
        self.m = m
        self.autoidx = 0

    def _add_submod(self, m: Module, name: str, inst: Instance):
        if name is None:
            name = f'i{self.autoidx}'
            self.autoidx += 1
        assert not hasattr(self.submodules, name)
        setattr(self.m.submodules, name, inst)

    def add_gate(self, m: Module, typ: str, name: str|None=None, **ports: dict[str, PortVal]):
        # TODO: gate golfing
        assert name in ("and2", "nand2", "or2", "nor2", "xor2", "xnor2",
            "mux2", "mux4", "mux8", "mux16", "buf", "clkbuf")
        inst = Instance(f"generic_{typ}",
            **{f'{"o" if p in ("x", "y", "q") else "i"}_{p}': q for p, q in ports}
        )
        self._add_submod(m: Module, name, inst)

    def avail_mux_sizes():
        return (2, 4, 8, 16)

    def add_mux(self, m: Module, inputs: list[PortVal], sel: list[PortVal], y: Signal, name=None):
        assert len(inputs) in self.avail_mux_sizes()
        assert len(sel) == len(inputs).bit_length()
        add_gate(m=m, type=f"mux{len(inputs)}", y=y, 
            **{f"i{i}": s for i, s in enumerate(inputs)},
            **{f"s{i}": s for i, s in enumerate(sel)}
        )

