from amaranth import *
from amaranth.lib import stream, wiring, data
from amaranth.lib.wiring import In, Out

class TapDemo(wiring.Component):
    rx: In(stream.Signature(data.StructLayout({
        "data": 8,
        "end":  1,
    })))
    tx: Out(stream.Signature(data.StructLayout({
        "data": 8,
        "end": 1,
    })))

    def elaborate(self, platform):
        m = Module()
        header = Signal(data.ArrayLayout(unsigned(8), 6+6+2))
        byte_count = Signal(range(1600))

        with m.FSM():
            with m.State("RX_IDLE"):
                m.d.comb += self.rx.ready.eq(1)
                m.d.sync += byte_count.eq(0)
                with m.If(self.rx.valid):
                    m.d.sync += byte_count.eq(byte_count + 1)
                    m.next = "RX_ACTIVE"
            with m.State("RX_ACTIVE"):
                m.d.comb += self.rx.ready.eq(1)
                with m.If(self.rx.valid):
                    m.d.sync += byte_count.eq(byte_count + 1)
                    with m.If(self.rx.payload.end):
                        m.next = "RX_END"
            with m.State("RX_END"):
                m.d.comb += self.rx.ready.eq(0)
                m.d.sync += Print(Format("src address: {:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x} ethertype: {:04x}",
                    *header[6:12],
                    Cat(*reversed(header[12:14]))))
                m.next = "RX_IDLE"
        with m.If(self.rx.valid & byte_count < len(header)):
            m.d.sync += header[byte_count].eq(self.rx.payload.data)

        return m

if __name__ == '__main__':
    from amaranth.cli import main
    main(TapDemo())
