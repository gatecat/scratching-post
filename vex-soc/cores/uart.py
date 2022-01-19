from amaranth import *

from amaranth_stdio.serial import AsyncSerialRX, AsyncSerialTX

from .peripheral import Peripheral

class UARTPeripheral(Peripheral, Elaboratable):
    def __init__(self, divisor, pins, **kwargs):
        super().__init__()

        self.divisor = divisor
        self.pins = pins

        bank            = self.csr_bank()
        self.tx_data    = bank.csr(8, "w")
        self.rx_data    = bank.csr(8, "r")

        self.tx_rdy     = bank.csr(1, "r")
        self.rx_avail    = bank.csr(1, "r")

        self._bridge    = self.bridge(data_width=32, granularity=8, alignment=2)
        self.bus        = self._bridge.bus

    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge  = self._bridge

        m.submodules.tx = tx = AsyncSerialTX(divisor=self.divisor)
        m.d.comb += [
            self.pins["tx_o"].eq(tx.o),
            self.pins["tx_oeb"].eq(0),
            tx.data.eq(self.tx_data.w_data),
            tx.ack.eq(self.tx_data.w_stb),
            self.tx_rdy.r_data.eq(tx.rdy)
        ]

        rx_buf = Signal(8)
        rx_avail = Signal()

        m.submodules.rx = rx = AsyncSerialRX(divisor=self.divisor)

        with m.If(self.rx_data.r_stb):
            m.d.sync += rx_avail.eq(0)

        with m.If(rx.rdy):
            m.d.sync += [
                rx_buf.eq(rx.data),
                rx_avail.eq(1)
            ]

        m.d.comb += [
            rx.i.eq(self.pins["rx_i"]),
            rx.ack.eq(~rx_avail),
            self.pins["rx_oeb"].eq(1),
            self.rx_data.r_data.eq(rx_buf),
            self.rx_avail.r_data.eq(rx_avail)
        ]

        return m
