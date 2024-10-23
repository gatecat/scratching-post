from amaranth import *
from amaranth.lib import stream, wiring, data
from amaranth.sim import Simulator, Tick

from .depacketiser import Depacketiser
import unittest

class TestDepacketiser(unittest.TestCase):
    def test_chip_select(self):
        ethernet_header = data.StructLayout({
            "ethertype": 16,
            "src_mac":  48,
            "dst_mac": 48,
        })
        dut = Depacketiser(ethernet_header)
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

