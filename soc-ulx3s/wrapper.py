from amaranth import *
from amaranth_boards.ulx3s import *
from amaranth_boards.ulx3s import *

from cores.spimemio_wrapper import QSPIPins
from cores.gpio import GPIOPins

class Ulx3sWrapper(Elaboratable):
    """
    This wrapper provides glue to simplify use of the ULX3S platform, and integrate between
    the Amaranth platform and the format of pins that the IP cores expect.
    """

    def get_flash(self, m, platform):
        plat_flash = platform.request("spi_flash", dir=dict(cs='-', copi='-', cipo='-', wp='-', hold='-'))

        flash = QSPIPins()
        # Flash clock requires a special primitive to access in ECP5
        m.submodules.usrmclk = Instance("USRMCLK",
            i_USRMCLKI=flash.clk_o,
            i_USRMCLKTS=ResetSignal(), # tristate in reset for programmer accesss
            a_keep=1,
        )
        # IO pins and buffers
        m.submodules += Instance("OBZ",
            o_O=plat_flash.cs.io,
            i_I=flash.csn_o,
            i_T=ResetSignal(),
        )
        # Pins in order
        data_pins = ["copi", "cipo", "wp", "hold"]

        for i in range(4):
            m.submodules += Instance("BB",
                io_B=getattr(plat_flash, data_pins[i]).io,
                i_I=flash.d_o[i],
                i_T=~flash.d_oe[i],
                o_O=flash.d_i[i]
            )
        return flash

    def get_led_gpio(self, m, platform):
        leds = GPIOPins(width=8)
        for i in range(8):
            led = platform.request("led", i)
            m.d.comb += led.o.eq(leds.o[i])
        return leds

    def elaborate(self, platform):
        clk25 = platform.request("clk25")
        m = Module()
        m.domains.sync = ClockDomain()
        m.d.comb += ClockSignal().eq(clk25.i)
        return m
