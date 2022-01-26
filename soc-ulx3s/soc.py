from amaranth import *
from amaranth_boards.ulx3s import *
from wrapper import Ulx3sWrapper

from amaranth_soc import wishbone

from amaranth_vexriscv.vexriscv import VexRiscv

from cores.gpio import GPIOPeripheral
from cores.spimemio_wrapper import SPIMemIO
from cores.uart import UARTPeripheral


class Ulx3sSoc(Ulx3sWrapper):
    def __init__(self):
        super().__init__()

        # Memory regions
        self.spi_base = 0x00000000

        # CSR regions
        self.spi_ctrl_base = 0xb0000000
        self.led_gpio_base = 0xb1000000
        self.uart_base = 0xb2000000
        self.timer_base = 0xb3000000

    def elaborate(self, platform):
        m = super().elaborate(platform)

        self._arbiter = wishbone.Arbiter(addr_width=30, data_width=32, granularity=8)
        self._decoder = wishbone.Decoder(addr_width=30, data_width=32, granularity=8)

        self.cpu = VexRiscv(config="LiteDebug", reset_vector=0x00100000)
        self._arbiter.add(self.cpu.ibus)
        self._arbiter.add(self.cpu.dbus)

        self.rom = SPIMemIO(flash=super().get_flash(m, platform))
        self._decoder.add(self.rom.data_bus, addr=self.spi_base)
        self._decoder.add(self.rom.ctrl_bus, addr=self.spi_ctrl_base)

        self.gpio = GPIOPeripheral(pins=super().get_led_gpio(m, platform))
        self._decoder.add(self.gpio.bus, addr=self.led_gpio_base)

        m.submodules.arbiter  = self._arbiter
        m.submodules.cpu      = self.cpu
        m.submodules.decoder  = self._decoder
        m.submodules.rom      = self.rom
        m.submodules.gpio     = self.gpio

        m.d.comb += [
            self._arbiter.bus.connect(self._decoder.bus),
            self.cpu.jtag_tck.eq(0),
            self.cpu.jtag_tdi.eq(0),
            self.cpu.jtag_tms.eq(0),
            self.cpu.software_irq.eq(0),
            self.cpu.timer_irq.eq(0),
        ]

        return m

if __name__ == "__main__":
    platform = ULX3S_85F_Platform()
    platform.build(Ulx3sSoc(), do_program=True)
