from amaranth import *
from amaranth.sim import Simulator, Delay, Settle
from amaranth_soc import wishbone

"""
Combined QSPI Flash and PSRAM controller for the demo SoC

This allows both XIP storage and main memory to be connected with a minimum number of external pins. 

It provides 4 8-bit control registers as well as a Wishbone bus interface.
The upper bit of the Wishbone bus selects flash (0) or RAM (1). Lower bits select chips and then
addresses within those chips.

The control registers are:

sys_cfg:
  bit 0: bitbang enable (wishbone access blocked; use bitbang registers for manual IO)
  bit 1: QSPI enable
  default: 0b00000000

pad_count:
  bits 3..0: padding bits for flash
  bits 7..4: padding bits for RAM
  default: 0x88

max_burst:
  bits 7..0: max burst length in words
  default: 0x10

  must be set so as to not violate the PSRAM maximum CS high time

bitbang:
  bit 0: read DI
  bit 1: write DO
  bit 2: write CLK
  bit 7..3: write CS

**IMPORTANT**: as some configuration will be required to take flash out of slow SPI mode, and bitbang
accesses cannot be done whilst running code in XIP mode; they system must have some other available
internal SRAM to copy the flash setup code into and run it out of.

For a further pin reduction, an "encoded" chip select mode is supported. An external active low decoder
such as the 74xx138 will be required.
"""
class QspiMem(Elaboratable):
    def __init__(self, *,
        num_flash=1, num_ram=6,
        flash_abits=24, ram_abits=23, encoded_cs=True):
        assert num_flash > 0 and num_ram > 0 # TODO: handle the one-type-only case
        self.num_flash = num_flash
        self.num_ram = num_ram
        self.flash_abits = flash_abits
        self.ram_abits = ram_abits
        self.encoded_cs = encoded_cs
        self.cs_count = num_ram + num_flash
        # total size of the flash address space
        self.flash_space = (flash_abits + (num_flash-1).bit_length())
        self.ram_space = (ram_abits + (num_ram-1).bit_length())
        self.total_space = max(self.flash_space, self.ram_space) # 1 extra bit to determine flash or RAM access
        self.data_bus = wishbone.Interface(addr_width=self.total_space-2, # -2 because WB has word addresses
                                      data_width=32, granularity=8)
        # the IO
        self.d_i = Signal(4)
        self.d_o = Signal(4)
        self.d_oe = Signal(4)
        self.clk_o = Signal()
        self.clk_oe = Signal()
        self.cs_width = self.cs_count.bit_length() if self.encoded_cs else self.cs_count
        self.cs_o = Signal(self.cs_width)
        self.cs_oe = Signal(self.cs_width)
        self.io = [self.d_i, self.d_o, self.d_oe,
            self.clk_o, self.clk_oe, self.cs_o, self.cs_oe]
        # config registers
        self.sys_cfg = Signal(8)
        self.pad_count = Signal(8)
        self.max_burst = Signal(8)
        self.bitbang_i = Signal(8)
        self.bitbang_o = Signal()
        self.config = [self.sys_cfg, self.pad_count, self.max_burst, self.bitbang_i]
    def elaborate(self, platform):
        m = Module()
        latched_adr = Signal(len(self.data_bus.adr))
        latched_we = Signal()
        counter = Signal(8)
        wait_count = Signal(4)
        sr = Signal(32)
        sr_shift = Signal(8)
        clk = Signal()
        dq_out = Signal(4)
        dq_oen = Signal(4)
        csn = Signal(self.cs_width)

        # Drive out clock on negedge while active
        m.domains += ClockDomain("neg", clk_edge="neg")
        m.d.comb += [
            ClockSignal("neg").eq(ClockSignal()),
            ResetSignal("neg").eq(ResetSignal()),
        ]
        with m.If(csn.all()):
            # Reset clock if nothing active
            m.d.neg += clk.eq(0)
        with m.Elif(counter.any()):
            m.d.neg += clk.eq(~clk)
            m.d.sync += counter.eq(counter-1)
        with m.If(counter.any()):
            # move shift register (sample/output data) on posedge
            pass
        # bitbang mode handling
        with m.FSM() as fsm:
            with m.State("IDLE"):
                m.d.sync += [
                    counter.eq(0),
                    csn.eq(C(-1, len(self.cs_o)))
                ]
        return m

def sim():
    m = Module()
    m.submodules.spi = spi = QspiMem()
    sim = Simulator(m)
    sim.add_clock(1e-6)
    def process():
        yield spi.sys_cfg.eq(0)
        yield spi.pad_count.eq(0x88)
        yield spi.max_burst.eq(0x10)
        yield spi.bitbang_i.eq(0)
        yield spi.data_bus.adr.eq(0x5A5A5A)
        yield spi.data_bus.sel.eq(1)
        yield spi.data_bus.we.eq(0)
        yield spi.data_bus.stb.eq(1)
        yield spi.data_bus.cyc.eq(1)
        for i in range(100):
            if (yield spi.data_bus.ack):
                yield spi.data_bus.stb.eq(0)
                yield spi.data_bus.cyc.eq(0)
            yield
    sim.add_sync_process(process)
    with sim.write_vcd("qspi.vcd", "qspi.gtkw"):
        sim.run()

if __name__ == '__main__':
    sim()
