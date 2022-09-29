from amaranth import *
from ..core.util import *
from enum import IntEnum

__all__ = ["BaseTech"]

class BaseTech:
    def __init__(self):
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
        self._add_submod(m, name, inst)

    def avail_mux_sizes(self):
        return (2, 4, 8, 16)

    def add_latch(self, m: Module, d: PortVal, e: PortVal, q: PortVal, name=None):
        inst = Instance(f"generic_lat",
            d=d, e=e, q=q
        )
        self._add_submod(m, name, inst)

    def add_dff(self, m: Module, d: PortVal, clk: PortVal, q: PortVal, name=None):
        inst = Instance(f"generic_dff",
            d=d, clk=clk, q=q
        )
        self._add_submod(m, name, inst)

    def add_mux(self, m: Module, inputs: list[PortVal], sel: list[PortVal], y: PortVal, name=None):
        assert len(inputs) in self.avail_mux_sizes()
        assert len(sel) == len(inputs).bit_length()
        add_gate(m=m, type=f"mux{len(inputs)}", y=y, 
            **{f"i{i}": s for i, s in enumerate(inputs)},
            **{f"s{i}": s for i, s in enumerate(sel)}
        )

    def split_mux(self, m: Module, inputs: list[tuple[PortVal, str]], sel: PortVal, y: PortVal, name=None, dry_run=False):
        # recursive muxtree decomposition into  tech-supported mux sizes, including multi-bit shared control muxes for
        # CGRA routing
        # returns an IntEnum containing the config bitmap of the mux -- running with dry_run gets the bitmap without
        # creating any logic
        if dry_run:
            sel = C(0, len(inputs).bit_length())
        else:
            assert len(sel) == len(inputs).bit_length()
        autoidx = 0
        bitmap = dict()
        if name is None and not dry_run:
            name = y.name
        def recursive_muxgen(inp_sigs, sel_bits, hot_bits):
            nonlocal autoidx
            nonlocal bitmap
            if len(inp_sigs) == 1:
                # terminal case
                bitmap[inp_sigs[0][1]] = hot_bits
                return inp_sigs[0][0]
            else:
                for mux_size in sorted(self.avail_mux_sizes()):
                    if mux_size >= len(inp_sigs):
                        break
                mux_depth = mux_size.bit_length()
                # TODO: check this dividing is correct
                chunks = []
                chunk_start = 0
                for i in range(mux_size):
                    chunk_end = (i + 1) * len(inp_sigs) // mux_size
                    chunk = inp_sigs[chunk_start:chunk_end]
                    if len(chunk) > 0:
                        chunks.append(chunk)
                    chunk_start = chunk_end
                # the recursive part
                for i in range(len(chunks)):
                    autoidx += 1
                    chunks[i] = recursive_muxgen(chunks[i], sel_bits[:-mux_depth],
                        hot_bits + list(((len(inp_sigs) - mux_depth) + j) for j in range(mux_depth) if i & (1 << j)))
                if not dry_run:
                    # the mux part
                    out_sig = Signal(name=f"{name}_n{autoidx}", shape=y.shape)
                    # might be switching multiple bits at once for CGRA interconnect...
                    for i in len(out_sig):
                        self.add_mux(m, inputs=([c[i] for c in chunks] + [0 for j in range(mux_size - len(chunks))]),
                            sel=sel_bits, y=out_sig[i], name=f"{name}_m{autoidx}")
                    return out_sig
                else:
                    return None
        result = recursive_muxgen(inputs, list(sel[i] for i in range(len(sel))), []) 
        if not dry_run:
            m.d.comb += y.eq(result)
        e = IntEnum(f"{name}_settings", {
            k: sum((1 << j) for j in v) for k, v in bitmap.items()
        })
        print(e)
        return e
