# amaranth: UnusedElaboratable=no

import unittest
from amaranth import *
from amaranth.sim import *

from .sram import AxiLiteSRAM
from .bus import Response, Decoder

class WishboneDecoderTestCase(unittest.TestCase):
    def test_simple_read(self):
        m = Module()
        m.submodules.sram0 = sram0 = AxiLiteSRAM(size=128, data_width=32, writable=False, init=range(32))
        m.submodules.sram1 = sram1 = AxiLiteSRAM(size=256, data_width=32, writable=False, init=range(5000, 5000+64))
        m.submodules.dut = dut = Decoder(addr_width=32, data_width=32)
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

        sim = Simulator(m)
        sim.add_clock(1e-6)
        sim.add_testbench(testbench)
        with sim.write_vcd(vcd_file="test_simple_dec_rd.vcd"):
            sim.run()

    def test_simple_write(self):
        m = Module()
        m.submodules.sram0 = sram0 = AxiLiteSRAM(size=128, data_width=32, writable=True)
        m.submodules.sram1 = sram1 = AxiLiteSRAM(size=256, data_width=32, writable=True)
        m.submodules.dut = dut = Decoder(addr_width=32, data_width=32)
        dut.add(sram0.bus, name="sram0")
        dut.add(sram1.bus, name="sram1")

        async def testbench(ctx):
            # Write something to sram0
            ctx.set(dut.bus.aw.payload.addr, 4)
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
            self.assertEqual(ctx.get(sram0._mem_data[1]), 0x12345678)

            # Write something to sram1
            ctx.set(dut.bus.aw.payload.addr, 256 + 4)
            ctx.set(dut.bus.aw.valid, 1)
            ctx.set(dut.bus.w.payload.data, 0xaabbccdd)
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
            self.assertEqual(ctx.get(sram1._mem_data[1]), 0xaabbccdd)

        sim = Simulator(m)
        sim.add_clock(1e-6)
        sim.add_testbench(testbench)
        with sim.write_vcd(vcd_file="test_simple_dec_wr.vcd"):
            sim.run()
