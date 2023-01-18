from amaranth import *
from amaranth.sim import Simulator, Delay, Settle
from amaranth_soc import wishbone

"""
Combined QSPI Flash and PSRAM controller for the demo SoC

This allows both XIP storage and main memory to be connected
with a minimum number of extra pins. 

For a further pin reduction, an "encoded" chip select mode
is supported.
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
        self.dmy_count = Signal(8)
        self.max_burst = Signal(8)
        self.bitbang = Signal(8)
        self.config = [self.sys_cfg, self.dmy_count, self.max_burst, self.bitbang]
    def elaborate(self, platform):
        m = Module()
        latched_adr = Signal(len(self.data_bus.adr))
        latched_we = Signal()
        counter = Signal(8)
        wait_count = Signal(4)
        sr = Signal(32)
        sr_shift = Signal(8)
        
