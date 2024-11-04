from amaranth import *
from amaranth.lib import stream, wiring, data
from amaranth.lib.wiring import In, Out

from .depacketiser import Depacketiser, HeaderEndianSwapper

ETHERNET_HEADER = data.StructLayout({
    "dst_mac": 48,
    "src_mac":  48,
    "ethertype": 16,
})

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
        m.submodules.depack = depack = Depacketiser(ETHERNET_HEADER)
        m.submodules.swapper = swapper = HeaderEndianSwapper(stream.Signature(ETHERNET_HEADER, always_ready=True))
        wiring.connect(m, wiring.flipped(self.rx), depack.bytes_in)
        wiring.connect(m, depack.header_out, swapper.header_in)

        m.d.comb += depack.payload_out.ready.eq(1)

        with m.If(swapper.header_out.valid):
            hdr = swapper.header_out.payload
            m.d.sync += Print(Format("dst_mac {:012x} src_mac {:012x} ethertype {:04x}",
                hdr.dst_mac, hdr.src_mac, hdr.ethertype))

        return m

if __name__ == '__main__':
    from amaranth.cli import main
    main(TapDemo())
