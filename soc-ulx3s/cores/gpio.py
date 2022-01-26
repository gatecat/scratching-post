from amaranth import *

from .peripheral import Peripheral

class GPIOPins(Record):
    def __init__(self, width):
        layout = [
            ("o", width),
            ("oe", width),
            ("i", width),
        ]
        super().__init__(layout)

class GPIOPeripheral(Peripheral, Elaboratable):
    def __init__(self, pins, **kwargs):
        super().__init__()

        self.width = len(pins.o)
        self.pins = pins

        bank            = self.csr_bank()
        self._dout      = bank.csr(self.width, "rw")
        self._oe        = bank.csr(self.width, "rw")
        self._din       = bank.csr(self.width, "r")

        self._bridge    = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus        = self._bridge.bus

    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge  = self._bridge

        dout_buf = Signal(self.width)
        oe_buf = Signal(self.width)

        with m.If(self._dout.w_stb): m.d.sync += dout_buf.eq(self._dout.w_data)
        with m.If(self._oe.w_stb): m.d.sync += oe_buf.eq(self._oe.w_data)

        m.d.comb += [
            self._dout.r_data.eq(dout_buf),
            self._oe.r_data.eq(oe_buf),
            self.pins.o.eq(dout_buf),
            self.pins.oe.eq(oe_buf),
        ]

        m.d.sync += self._din.r_data.eq(self.pins.i)

        return m
