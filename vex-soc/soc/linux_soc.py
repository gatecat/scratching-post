import argparse
import importlib

from amaranth import *
from amaranth_soc import wishbone

from cores.vexriscv_wrapper import Vexriscv
from cores.gpio import GPIOPeripheral
from cores.spimemio_wrapper import SPIMemIO
from cores.hyperram import HyperRAM

class LinuxSoC(Elaboratable):
    def __init__(self, *, flash_pins, uart_pins, hyperram0_pins, hyperram1_pins, gpio_pins, gpio_count, jtag_pins):

        spi_base = 0x00000000
        ram0_base = 0x10000000
        ram1_base = ram0_base + (8*1024*1024)

        spi_ctrl_base = 0xb0000000
        gpio_base = 0xb1000000

        self._arbiter = wishbone.Arbiter(addr_width=30, data_width=32, granularity=8)
        self._decoder = wishbone.Decoder(addr_width=30, data_width=32, granularity=8)

        self.cpu = Vexriscv()
        self._arbiter.add(self.cpu.ibus)
        self._arbiter.add(self.cpu.dbus)

        self.jtag_pins = jtag_pins

        self.rom = SPIMemIO(flash=flash_pins)
        self._decoder.add(self.rom.data_bus, addr=spi_base)
        self._decoder.add(self.rom.ctrl_bus, addr=spi_ctrl_base)

        self.hyperram0 = HyperRAM(io=hyperram0_pins, index=0)
        self._decoder.add(self.hyperram0.bus, addr=ram0_base)

        self.hyperram1 = HyperRAM(io=hyperram1_pins, index=1)
        self._decoder.add(self.hyperram1.bus, addr=ram1_base)

        self.gpio = GPIOPeripheral(gpio_count, gpio_pins)
        self._decoder.add(self.gpio.bus, addr=gpio_base)

        self.memory_map = self._decoder.bus.memory_map

    def elaborate(self, platform):
        m = Module()

        m.submodules.arbiter  = self._arbiter
        m.submodules.cpu      = self.cpu

        m.submodules.decoder  = self._decoder
        m.submodules.rom      = self.rom
        m.submodules.hyperram0 = self.hyperram0
        m.submodules.hyperram1 = self.hyperram1
        m.submodules.gpio     = self.gpio

        m.d.comb += [
            self._arbiter.bus.connect(self._decoder.bus),
            self.cpu.jtag_tck.eq(self.jtag_pins["tck_i"]),
            self.cpu.jtag_tdi.eq(self.jtag_pins["tdi_i"]),
            self.cpu.jtag_tms.eq(self.jtag_pins["tms_i"]),
            self.jtag_pins["tdo_o"].eq(self.cpu.jtag_tdo),
            self.jtag_pins["tck_oeb"].eq(1),
            self.jtag_pins["tdi_oeb"].eq(1),
            self.jtag_pins["tms_oeb"].eq(1),
            self.jtag_pins["tdo_oeb"].eq(0),
            self.cpu.software_irq.eq(0),
            self.cpu.timer_irq.eq(0),
            self.cpu.ext_irq.eq(0)
        ]

        return m

# Create a pretend UART resource with arbitrary signals
class UARTPins():
    class Input():
        def __init__(self, sig):
            self.i = sig
    class Output():
        def __init__(self, sig):
            self.o = sig
    def __init__(self, rx, tx):
        self.rx = UARTPins.Input(rx)
        self.tx = UARTPins.Output(tx)


class SoCWrapper(Elaboratable):
    def __init__(self, build_dir="build"):
        io_count = 38
        self.build_dir = build_dir
        self.io_in = Signal(io_count)
        self.io_out = Signal(io_count)
        self.io_oeb = Signal(io_count)
        self.pinout = {
            "clk": 0,
            "rstn": 1,
            "flash_clk": 2,
            "flash_csn": 3,
            "flash_d0": 4,
            "flash_d1": 5,
            "flash_d2": 6,
            "flash_d3": 7,
            "ram0_clk": 8,
            "ram0_csn": 9,
            "ram0_rwds": 10,
            "ram0_d0": 11,
            "ram0_d1": 12,
            "ram0_d2": 13,
            "ram0_d3": 14,
            "ram0_d4": 15,
            "ram0_d5": 16,
            "ram0_d6": 17,
            "ram0_d7": 18,
            "ram1_clk": 19,
            "ram1_csn": 20,
            "ram1_rwds": 21,
            "ram1_d0": 22,
            "ram1_d1": 23,
            "ram1_d2": 24,
            "ram1_d3": 25,
            "ram1_d4": 26,
            "ram1_d5": 27,
            "ram1_d6": 28,
            "ram1_d7": 29,
            "uart_tx": 30,
            "uart_rx": 31,
            "jtag_tck": 32,
            "jtag_tdi": 33,
            "jtag_tms": 34,
            "jtag_tdo": 35,
            "gpio_0": 36,
            "gpio_1": 37,
        }

    def i(self, name): return self.io_in[self.pinout[name]]
    def o(self, name): return self.io_out[self.pinout[name]]
    def oeb(self, name): return self.io_oeb[self.pinout[name]]

    def elaborate(self, platform):
        m = Module()

        # Gets i, o, oeb in a dict for all pins starting with a prefix
        def resource_pins(resource):
            result = {}
            for pin, bit in self.pinout.items():
                if pin.startswith(resource):
                    bit_name = pin[len(resource):]
                    result[f"{bit_name}_i"] = Signal()
                    result[f"{bit_name}_o"] = Signal()
                    result[f"{bit_name}_oeb"] = Signal()
                    m.d.comb += [
                        self.io_out[bit].eq(result[f"{bit_name}_o"]),
                        self.io_oeb[bit].eq(result[f"{bit_name}_oeb"]),
                        result[f"{bit_name}_i"].eq(self.io_in[bit]),
                    ]
            return result

        # Clock input
        m.domains.sync = ClockDomain(async_reset=False)
        m.d.comb += ClockSignal().eq(self.i("clk"))
        # Reset synchroniser
        rst = Signal()
        m.d.comb += rst.eq(~self.i("rstn"))
        rst_sync0 = Signal(reset_less=True)
        rst_sync1 = Signal(reset_less=True)
        m.d.sync += [
            rst_sync0.eq(rst),
            rst_sync1.eq(rst_sync0),
        ]
        m.d.comb += [
            ResetSignal().eq(rst_sync1),
        ]

        uart_pins = UARTPins(rx=self.i("uart_rx"), tx=self.o("uart_tx"))

        # The SoC itself
        m.submodules.soc = LinuxSoC(
            flash_pins=resource_pins("flash_"),
            uart_pins=uart_pins,
            hyperram0_pins=resource_pins("ram0_"),
            hyperram1_pins=resource_pins("ram1_"),
            gpio_count=2, gpio_pins=resource_pins("gpio_"),
            jtag_pins=resource_pins("jtag_")
        )

        # Remaining pins
        for pin, bit in self.pinout.items():
            if pin in ("clk", "rstn", "uart_rx") or pin.startswith("unalloc_"): # inputs and TODOs
                m.d.comb += [
                    self.io_oeb[bit].eq(1),
                    self.io_out[bit].eq(0),
                ]
            elif pin.startswith("heartbeat") or pin in ("rst_inv_out", "rst_sync_out", "uart_tx"): # outputs
                m.d.comb += [
                    self.io_oeb[bit].eq(0),
                ]
        return m

if __name__ == "__main__":
    wrapper = SoCWrapper()
    from amaranth.cli import main
    main(wrapper, name="soc_wrapper", ports=[wrapper.io_in, wrapper.io_out, wrapper.io_oeb])
