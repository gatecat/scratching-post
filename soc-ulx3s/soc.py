from amaranth import *
from amaranth_boards.ulx3s import *

class Ulx3sSoc(Elaboratable):
    def elaborate(self, platform):
        clk25 = platform.request("clk25")
        m = Module()
        m.domains.sync = ClockDomain()
        m.d.comb += ClockSignal().eq(clk25.i)
        flash = platform.request("spi_flash", dir=dict(cs='o', copi='-', cipo='-', wp='-', hold='-'))
        print(flash)
        return m

if __name__ == "__main__":
    platform = ULX3S_85F_Platform()
    platform.build(Ulx3sSoc(), do_program=True)
