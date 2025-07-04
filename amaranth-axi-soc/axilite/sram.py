from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In
from amaranth.lib.memory import MemoryData, Memory
from amaranth.utils import ceil_log2, exact_log2

from amaranth_soc.memory import MemoryMap

from .bus import Signature, Response


__all__ = ["AxiLiteSRAM"]

class AxiLiteSRAM(wiring.Component):
    def __init__(self, *, size, data_width, addr_width=None, writable=True, init=()):

        if addr_width is None:
            addr_width = ceil_log2(size)

        self._size     = size
        self._addr_width = addr_width
        self._data_width = data_width
        self._writable = bool(writable)
        self._mem_data = MemoryData(depth=(size * 8) // data_width,
                                    shape=unsigned(data_width), init=init)
        self._mem      = Memory(self._mem_data)

        super().__init__({"bus": In(Signature(addr_width=addr_width,
            data_width=data_width))})

        self.bus.memory_map = MemoryMap(addr_width=exact_log2(size), data_width=8)
        self.bus.memory_map.add_resource(self._mem, name=("mem",), size=size)
        self.bus.memory_map.freeze()


        @property
        def size(self):
            return self._size

        @property
        def writable(self):
            return self._writable

        @property
        def init(self):
            return self._mem_data.init

        @init.setter
        def init(self, init):
            self._mem_data.init = init

    def elaborate(self, platform):
        m = Module()
        m.submodules.mem = self._mem

        rd_valid = Signal()
        wr_valid = Signal()
        grant_wr_or_rd = Signal()
        last_wr_or_rd = Signal()

        # Share a single mem_addr signal so the single port RAM is inferred
        mem_addr = Signal(self._addr_width)
        mem_bounds_check = Signal()
        mem_wren = Signal()

        # Offset between byte (AXI) and word (memory) addresses
        addr_start = exact_log2(self._data_width // 8)

        # Generate internal enable signals
        m.d.comb += [rd_valid.eq(0), wr_valid.eq(0)]
        with m.If(self.bus.ar.valid & self.bus.r.ready):
            m.d.comb += rd_valid.eq(1)
        if self._writable:
            with m.If(self.bus.aw.valid & self.bus.w.valid & self.bus.b.ready):
                m.d.comb += wr_valid.eq(1)

        # Assume a single port memory, so we need to arbitrate between read and write
        m.d.comb += grant_wr_or_rd.eq(0)
        with m.If(rd_valid & wr_valid):
            m.d.comb += grant_wr_or_rd.eq(~last_wr_or_rd) # round-robin
            m.d.sync += last_wr_or_rd.eq(grant_wr_or_rd)
        with m.Elif(rd_valid):
            m.d.comb += grant_wr_or_rd.eq(0)
            m.d.sync += last_wr_or_rd.eq(0)
        with m.Elif(wr_valid):
            m.d.comb += grant_wr_or_rd.eq(1)
            m.d.sync += last_wr_or_rd.eq(1)


        # Memory access generation
        read_port = self._mem.read_port()
        with m.If(rd_valid & ~grant_wr_or_rd):
            m.d.comb += [
                mem_addr.eq(self.bus.ar.payload.addr),
                mem_wren.eq(0),
                self.bus.ar.ready.eq(1),
            ]

        m.d.comb += [
            read_port.addr.eq(mem_addr[addr_start:]),
            read_port.en.eq(~mem_wren & rd_valid & ~grant_wr_or_rd),
            self.bus.r.payload.data.eq(read_port.data),
        ]

        if self._writable:
            write_port = self._mem.write_port()

            with m.If(wr_valid & grant_wr_or_rd):
                m.d.comb += [
                    mem_addr.eq(self.bus.aw.payload.addr),
                    mem_wren.eq(mem_bounds_check),
                    self.bus.aw.ready.eq(1),
                    self.bus.w.ready.eq(1),
                ]

            m.d.comb += [
                write_port.addr.eq(mem_addr[addr_start:]),
                write_port.en.eq(Mux(mem_wren, self.bus.w.payload.strb, 0)),
                write_port.data.eq(self.bus.w.payload.data),
            ]

        # Bounds check
        m.d.comb += mem_bounds_check.eq(mem_addr < self._size)

        # Response generation (one cycle later)
        with m.If(self.bus.r.ready):
            m.d.sync += self.bus.r.valid.eq(0)
        with m.If(self.bus.b.ready):
            m.d.sync += self.bus.b.valid.eq(0)

        with m.If(rd_valid & ~grant_wr_or_rd):
            m.d.sync += [
                self.bus.r.valid.eq(1),
                self.bus.r.payload.resp.eq(Mux(mem_bounds_check, Response.OKAY, Response.SLVERR))
            ]
        if self._writable:
            with m.If(wr_valid & grant_wr_or_rd):
                m.d.sync += [
                    self.bus.b.valid.eq(1),
                    self.bus.b.payload.resp.eq(Mux(mem_bounds_check, Response.OKAY, Response.SLVERR))
                ]

        return m


