# amaranth: UnusedElaboratable=no

import unittest
from amaranth import *
from amaranth.sim import *

from .sram import AxiLiteSRAM
from .bus import Response, Decoder

class WishboneDecoderTestCase(unittest.TestCase):
    def test_simple_read(self):
        sram0 = AxiLiteSRAM(size=128, data_width=32, writable=False, init=range(32))
        sram1 = AxiLiteSRAM(size=256, data_width=32, writable=False, init=range(5000, 5000+64))
        dut = Decoder(addr_width=32, data_width=32)
        dut.add(sram0.bus, name="sram0")
        dut.add(sram1.bus, name="sram1")

        async def testbench(ctx):
            for i in range(32):
                ctx.set(dut.bus.ar.payload.addr, i * 4)
                ctx.set(dut.bus.ar.valid, 1)
                ctx.set(dut.bus.r.ready, 1)
                self.assertEqual(ctx.get(dut.bus.ar.ready), 1)
                await ctx.tick()
                self.assertEqual(ctx.get(dut.bus.r.valid), 1)
                self.assertEqual(ctx.get(dut.bus.r.payload.resp), Response.OKAY)
                self.assertEqual(ctx.get(dut.bus.r.payload.data), i)
                ctx.set(dut.bus.ar.valid, 0)
                await ctx.tick()

            for i in range(64):
                ctx.set(dut.bus.ar.payload.addr, 256 + i * 4)
                ctx.set(dut.bus.ar.valid, 1)
                ctx.set(dut.bus.r.ready, 1)
                self.assertEqual(ctx.get(dut.bus.ar.ready), 1)
                await ctx.tick()
                self.assertEqual(ctx.get(dut.bus.r.valid), 1)
                self.assertEqual(ctx.get(dut.bus.r.payload.resp), Response.OKAY)
                self.assertEqual(ctx.get(dut.bus.r.payload.data), 5000+i)
                ctx.set(dut.bus.ar.valid, 0)
                await ctx.tick()

        sim = Simulator(dut)
        sim.add_clock(1e-6)
        sim.add_testbench(testbench)
        with sim.write_vcd(vcd_file="test_simple_dec.vcd"):
            sim.run()
