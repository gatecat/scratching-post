from amaranth import *
from amaranth.lib import stream, wiring, data
from amaranth.lib.wiring import In, Out

from amaranth.sim import Simulator, Tick

from .depacketiser import Depacketiser, HeaderEndianSwapper
import unittest

ETHERNET_HEADER = data.StructLayout({
    "dst_mac": 48,
    "src_mac":  48,
    "ethertype": 16,
})

class DepacketiserHarness(wiring.Component):
    def __init__(self):
        super().__init__({
            "bytes_in": In(stream.Signature(data.StructLayout({
                "data": 8,
                "end":  1,
            }))),
            "header_out": Out(stream.Signature(ETHERNET_HEADER, always_ready=True)),
            "payload_out": Out(stream.Signature(data.StructLayout({
                "data": 8,
                "end":  1,
            }))),
            "error": Out(1),
        })

    def elaborate(self, platform):
        m = Module()
        m.submodules.depack = depack = Depacketiser(ETHERNET_HEADER)
        m.submodules.swapper = swapper = HeaderEndianSwapper(stream.Signature(ETHERNET_HEADER, always_ready=True))
        wiring.connect(m, wiring.flipped(self.bytes_in), depack.bytes_in)
        wiring.connect(m, depack.header_out, swapper.header_in)
        wiring.connect(m, swapper.header_out, wiring.flipped(self.header_out))
        wiring.connect(m, depack.payload_out, wiring.flipped(self.payload_out))
        m.d.comb += self.error.eq(depack.error)
        return m

class TestDepacketiser(unittest.TestCase):
    def test_chip_select(self):
        ethernet_header = data.StructLayout({
            "dst_mac": 48,
            "src_mac":  48,
            "ethertype": 16,
        })
        dut = DepacketiserHarness()
        def testbench():
            packet = [0x12, 0x34, 0x56, 0x78, 0xAB, 0xCD,
                0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF,
                0x08, 0x00]
            yield Tick()
            for i, b in enumerate(packet):
                yield dut.bytes_in.valid.eq(1)
                yield dut.bytes_in.payload.data.eq(b)
                yield dut.bytes_in.payload.end.eq(i == len(packet) - 1)
                yield Tick()
            yield dut.bytes_in.valid.eq(0)
            yield Tick()
            header = yield dut.header_out.payload.dst_mac
            print(f"{yield dut.header_out.payload.dst_mac:012x} {yield dut.header_out.payload.src_mac:012x} {yield dut.header_out.payload.ethertype:04x}")
        sim = Simulator(dut)
        sim.add_clock(1e-5)
        sim.add_testbench(testbench)
        with sim.write_vcd("depacketiser_test.vcd", "depacketiser_test.gtkw"):
            sim.run()

if __name__ == "__main__":
    unittest.main()

