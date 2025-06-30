# amaranth: UnusedElaboratable=no

import unittest
from amaranth import *
from amaranth.sim import *

from .sram import AxiLiteSRAM
from .bus import Response

class WishboneSRAMTestCase(unittest.TestCase):
    def test_simple_read(self):
        dut = AxiLiteSRAM(size=128, data_width=32, writable=False, init=range(32))

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

        sim = Simulator(dut)
        sim.add_clock(1e-6)
        sim.add_testbench(testbench)
        with sim.write_vcd(vcd_file="test_simple_read.vcd"):
            sim.run()

    def test_arbitration(self):
        dut = AxiLiteSRAM(size=128, data_width=32, writable=True, init=range(32))

        async def testbench(ctx):
            # Write something
            ctx.set(dut.bus.aw.payload.addr, 0x4)
            ctx.set(dut.bus.aw.valid, 1)
            ctx.set(dut.bus.w.payload.data, 0x12345678)
            ctx.set(dut.bus.w.payload.strb, 0b1111)
            ctx.set(dut.bus.w.valid, 1)
            ctx.set(dut.bus.b.ready, 1)
            self.assertEqual(ctx.get(dut.bus.aw.ready), 1)
            await ctx.tick()
            self.assertEqual(ctx.get(dut.bus.b.valid), 1)
            self.assertEqual(ctx.get(dut.bus.b.payload.resp), Response.OKAY)
            ctx.set(dut.bus.aw.valid, 0)
            ctx.set(dut.bus.w.valid, 0)
            await ctx.tick()
            self.assertEqual(ctx.get(dut._mem_data[1]), 0x12345678)

            # Trigger both a ready and a write at the same time

            ctx.set(dut.bus.aw.payload.addr, 0x8)
            ctx.set(dut.bus.aw.valid, 1)
            ctx.set(dut.bus.w.payload.data, 0xAABBCCDD)
            ctx.set(dut.bus.w.payload.strb, 0b1111)
            ctx.set(dut.bus.w.valid, 1)
            ctx.set(dut.bus.b.ready, 1)

            ctx.set(dut.bus.ar.payload.addr, 0x4)
            ctx.set(dut.bus.ar.valid, 1)
            ctx.set(dut.bus.r.ready, 1)

            # Last was a write, so read should be accepted first
            self.assertEqual(ctx.get(dut.bus.ar.ready), 1)
            await ctx.tick()
            self.assertEqual(ctx.get(dut.bus.r.valid), 1)
            self.assertEqual(ctx.get(dut.bus.r.payload.resp), Response.OKAY)
            self.assertEqual(ctx.get(dut.bus.r.payload.data), 0x12345678)
            ctx.set(dut.bus.ar.valid, 0)
            # Now the write is accepted
            self.assertEqual(ctx.get(dut.bus.aw.ready), 1)
            await ctx.tick()
            self.assertEqual(ctx.get(dut.bus.b.valid), 1)
            self.assertEqual(ctx.get(dut.bus.b.payload.resp), Response.OKAY)
            ctx.set(dut.bus.aw.valid, 0)
            ctx.set(dut.bus.w.valid, 0)
            await ctx.tick()
            self.assertEqual(ctx.get(dut._mem_data[2]), 0xAABBCCDD)


        sim = Simulator(dut)
        sim.add_clock(1e-6)
        sim.add_testbench(testbench)
        with sim.write_vcd(vcd_file="test_arbitration.vcd"):
            sim.run()

