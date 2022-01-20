from amaranth import *
from amaranth.utils import log2_int

from amaranth_soc import wishbone
from amaranth_soc.memory import MemoryMap
from amaranth_soc.periph import ConstantMap

from .peripheral import Peripheral

class SRAMPeripheral(Peripheral, Elaboratable):
    """SRAM storage peripheral.

    Parameters
    ----------
    size : int
        Memory size in bytes.
    data_width : int
        Bus data width.
    granularity : int
        Bus granularity.
    writable : bool
        Memory is writable.

    Attributes
    ----------
    bus : :class:`amaranth_soc.wishbone.Interface`
        Wishbone bus interface.
    """
    # TODO raise bus.err if read-only and a bus write is attempted.
    def __init__(self, *, size, data_width=32, granularity=8, writable=True, index=0):
        super().__init__()

        if not isinstance(size, int) or size <= 0 or size & size-1:
            raise ValueError("Size must be an integer power of two, not {!r}"
                             .format(size))
        if size < data_width // granularity:
            raise ValueError("Size {} cannot be lesser than the data width/granularity ratio "
                             "of {} ({} / {})"
                              .format(size, data_width // granularity, data_width, granularity))

        self._mem = Memory(depth=(size * granularity) // data_width, width=data_width, simulate=False)

        self.bus = wishbone.Interface(addr_width=log2_int(self._mem.depth),
                                      data_width=self._mem.width, granularity=granularity)

        map = MemoryMap(addr_width=log2_int(size), data_width=granularity, name=self.name)
        map.add_resource(name=f"sram{index}", size=size, resource=self._mem)
        self.bus.memory_map = map

        self.size        = size
        self.granularity = granularity
        self.writable    = writable

    @property
    def init(self):
        return self._mem.init

    @init.setter
    def init(self, init):
        self._mem.init = init

    @property
    def constant_map(self):
        return ConstantMap(
            SIZE = self.size,
        )

    def elaborate(self, platform):
        m = Module()

        incr = Signal.like(self.bus.adr)


        m.submodules.mem_rp = mem_rp = self._mem.read_port()
        m.d.comb += self.bus.dat_r.eq(mem_rp.data)

        with m.If(self.bus.cyc & self.bus.stb):
            m.d.sync += self.bus.ack.eq(1)
            m.d.comb += mem_rp.addr.eq(self.bus.adr)

        with m.If(self.bus.ack):
            m.d.sync += self.bus.ack.eq(0)

        if self.writable:
            m.submodules.mem_wp = mem_wp = self._mem.write_port(granularity=self.granularity)
            m.d.comb += mem_wp.addr.eq(mem_rp.addr)
            m.d.comb += mem_wp.data.eq(self.bus.dat_w)
            with m.If(self.bus.cyc & self.bus.stb & self.bus.we):
                m.d.comb += mem_wp.en.eq(self.bus.sel)

        return m
