import argparse
import importlib

from amaranth import *
from amaranth_soc import wishbone

from cores.vexriscv_wrapper import Vexriscv
from cores.gpio import GPIOPeripheral
from cores.spimemio_wrapper import SPIMemIO
from cores.sram import SRAMPeripheral
from cores.uart import UARTPeripheral
from cores.platform_timer import PlatformTimer
from cores.soc_id import SoCID

class SimLinuxSoC(Elaboratable):
    def __init__(self, *, flash_pins, uart_pins, gpio_pins, gpio_count):

        spi_base = 0x00000000
        ram0_base = 0x10000000
        ram1_base = ram0_base + (8*1024*1024)

        spi_ctrl_base = 0xb0000000
        gpio_base = 0xb1000000
        uart_base = 0xb2000000
        timer_base = 0xb3000000
        soc_id_base = 0xb4000000

        self._arbiter = wishbone.Arbiter(addr_width=30, data_width=32, granularity=8)
        self._decoder = wishbone.Decoder(addr_width=30, data_width=32, granularity=8)

        self.cpu = Vexriscv()
        self._arbiter.add(self.cpu.ibus)
        self._arbiter.add(self.cpu.dbus)

        self.rom = SPIMemIO(flash=flash_pins)
        # self._decoder.add(self.rom.data_bus, addr=spi_base)
        self._decoder.add(self.rom.ctrl_bus, addr=spi_ctrl_base)

        self.sim_rom = SRAMPeripheral(size=16*1024*1024, index=2)
        self._decoder.add(self.sim_rom.bus, addr=spi_base)

        self.hyperram0 = SRAMPeripheral(size=8*1024*1024, index=0)
        self._decoder.add(self.hyperram0.bus, addr=ram0_base)

        self.hyperram1 = SRAMPeripheral(size=8*1024*1024, index=1)
        self._decoder.add(self.hyperram1.bus, addr=ram1_base)

        self.gpio = GPIOPeripheral(gpio_count, gpio_pins)
        self._decoder.add(self.gpio.bus, addr=gpio_base)

        self.uart = UARTPeripheral(divisor=(27000000//115200), pins=uart_pins)
        self._decoder.add(self.uart.bus, addr=uart_base)

        self.timer = PlatformTimer(width=48)
        self._decoder.add(self.timer.bus, addr=timer_base)

        self.soc_id = SoCID(type_id=0xca7f100f)
        self._decoder.add(self.soc_id.bus, addr=soc_id_base)

        self.memory_map = self._decoder.bus.memory_map

    def elaborate(self, platform):
        m = Module()

        m.submodules.arbiter  = self._arbiter
        m.submodules.cpu      = self.cpu

        m.submodules.decoder  = self._decoder
        m.submodules.rom      = self.rom
        m.submodules.sim_rom  = self.sim_rom
        m.submodules.hyperram0 = self.hyperram0
        m.submodules.hyperram1 = self.hyperram1
        m.submodules.gpio     = self.gpio
        m.submodules.uart     = self.uart
        m.submodules.timer     = self.timer
        m.submodules.soc_id   = self.soc_id

        m.d.comb += [
            self._arbiter.bus.connect(self._decoder.bus),
            self.cpu.jtag_tck.eq(0),
            self.cpu.jtag_tdi.eq(0),
            self.cpu.jtag_tms.eq(0),
            self.cpu.software_irq.eq(0),
            self.cpu.timer_irq.eq(self.timer.timer_irq),
            self.cpu.ext_irq.eq(0)
        ]

        return m


class SimMonitor(Elaboratable):
    def __init__(self, name, bus, verilog_boxes):
        self.name = name
        self.pins = []
        for field, width, _ in bus.layout:
            self.pins.append((field, width, getattr(bus, field)))
        if name not in verilog_boxes:
            verilog_boxes[self.name] = f"(* blackbox, cxxrtl_blackbox, keep *) module {name} (\n"
            verilog_pins = ['(* cxxrtl_edge="a" *) input clk']
            for field, width, _  in self.pins:
                verilog_pins.append(f'input [{width-1}:0] {field}')
            verilog_boxes[self.name] += ",\n".join(verilog_pins)
            verilog_boxes[self.name] += "\n);\n"
            verilog_boxes[self.name] += "endmodule\n"
    def elaborate(self, platform):
        m = Module()
        conn = dict(i_clk=ClockSignal(), a_keep=True)
        for field, width, subsig in self.pins:
            conn[f'i_{field}'] = subsig
        m.submodules.bb = Instance(self.name, **conn)
        return m

class SimPeripheral(Elaboratable):
    def __init__(self, name, pins, verilog_boxes):
        self.name = name
        self.io = {}
        self.pins = [(p.replace(">", ""), w) for p, w in pins]
        for pin, w in self.pins:
            for i in range(w):
                bit_name = f"{pin}{i}" if w > 1 else pin
                self.io[f"{bit_name}_i"] = Signal()
                self.io[f"{bit_name}_o"] = Signal()
                self.io[f"{bit_name}_oeb"] = Signal()
        if name not in verilog_boxes:
            verilog_boxes[self.name] = f"(* blackbox, cxxrtl_blackbox, keep *) module {name} (\n"
            verilog_pins = []
            for pin, w in pins:
                bb_pin = "periph" if len(pin) == 0 else pin.replace(">", "")
                verilog_pins.append(f"    output [{w-1}:0] {bb_pin}_i")
                edge = '(* cxxrtl_edge="a" *)' if '>' in pin else ''
                verilog_pins.append(f"{edge}    input  [{w-1}:0] {bb_pin}_o")
                verilog_pins.append(f"    input  [{w-1}:0] {bb_pin}_oeb")
            verilog_boxes[self.name] += ",\n".join(verilog_pins)
            verilog_boxes[self.name] += "\n);\n"
            verilog_boxes[self.name] += "endmodule\n"

    def elaborate(self, platform):
        m = Module()
        conn = dict(a_keep=True)
        for pin, w in self.pins:
            sig_i = Signal(w)
            sig_o = Signal(w)
            sig_oeb = Signal(w)
            bb_pin = "periph" if len(pin) == 0 else pin
            conn[f"o_{bb_pin}_i"] = sig_i
            conn[f"i_{bb_pin}_o"] = sig_o
            conn[f"i_{bb_pin}_oeb"] = sig_oeb
            for i in range(w):
                bit_name = f"{pin}{i}" if w > 1 else pin
                m.d.comb += self.io[f"{bit_name}_i"].eq(sig_i[i])
                m.d.comb += sig_o[i].eq(self.io[f"{bit_name}_o"])
                m.d.comb += sig_oeb[i].eq(self.io[f"{bit_name}_oeb"])
        m.submodules.bb = Instance(self.name, **conn)
        return m

def write_boxes(f, verilog_boxes):
    for _, box in sorted(verilog_boxes.items(), key=lambda x: x[0]):
        print(box, file=f)

# SoC top
class SimSoC(Elaboratable):
    def __init__(self, build_dir="cxxsim/build"):
        self.clk = Signal()
        self.rst = Signal()
        self.uart_tx = Signal()
        self.build_dir = build_dir

    def elaborate(self, platform):
        m = Module()
        m.domains.sync = ClockDomain(async_reset=False)
        m.d.comb += ClockSignal().eq(self.clk)
        m.d.comb += ResetSignal().eq(self.rst)

        verilog_boxes = {}

        # SPI flash
        spiflash = SimPeripheral("spiflash_model", [(">clk", 1), (">csn", 1), ("d", 4)], verilog_boxes)
        m.submodules.spiflash = spiflash

        # GPIO
        gpio = SimPeripheral("gpio_model", [("", 2), ], verilog_boxes)
        m.submodules.gpio = gpio

        # UART
        uart = SimPeripheral("uart_model", [("tx", 1), ("rx", 1)], verilog_boxes)
        m.submodules.uart = uart
        m.d.comb += self.uart_tx.eq(uart.io["tx_o"])

        # The SoC itself
        m.submodules.soc = SimLinuxSoC(flash_pins=spiflash.io, uart_pins=uart.io, gpio_pins=gpio.io, gpio_count=2)

        bus_mon = SimMonitor("wb_mon", m.submodules.soc._arbiter.bus, verilog_boxes)
        m.submodules.bus_mon = bus_mon

        with open(f"{self.build_dir}/sim_blackboxes.v", "w") as f:
            write_boxes(f, verilog_boxes)
        return m

if __name__ == "__main__":
    sim_top = SimSoC()
    from amaranth.cli import main
    main(sim_top, name="sim_top", ports=[sim_top.clk, sim_top.rst, sim_top.uart_tx])

