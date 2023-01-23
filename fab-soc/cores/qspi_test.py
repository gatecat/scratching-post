import sys
from pathlib import Path

from amaranth import *
from amaranth.sim import Simulator, Delay, Settle, Passive

from qspi_model import QspiModel
from qspi_mem import QspiMem

import traceback

def run_tests():

    m = Module()
    model = QspiModel()
    m.submodules.spi = spi = QspiMem()
    Path("test_results").mkdir(parents=True, exist_ok=True)

    def wb_xfer(addr, write_data=None, write_sel=0b1111, timeout=1000):
        yield spi.data_bus.adr.eq(addr)
        yield spi.data_bus.sel.eq(write_sel)
        yield spi.data_bus.we.eq(write_data is not None)
        yield spi.data_bus.dat_w.eq(write_data or 0)
        yield spi.data_bus.stb.eq(1)
        yield spi.data_bus.cyc.eq(1)
        result = None
        for i in range(timeout):
            if (yield spi.data_bus.ack):
                result = yield spi.data_bus.dat_r
                yield spi.data_bus.stb.eq(0)
                yield spi.data_bus.cyc.eq(0)
                yield
                break
            yield
        return result

    def _cfg_spi():
        yield spi.sys_cfg.eq(0)
        yield spi.pad_count.eq(0x88)
        yield spi.max_burst.eq(0x10)

    def _cfg_quad():
        yield spi.sys_cfg.eq(2)
        yield spi.pad_count.eq(0x64)
        yield spi.max_burst.eq(0x10)

    def test_flash_spi_read():
        yield from _cfg_spi()
        model.data[0][(0x1234 << 2) | 0] = 0xEF
        model.data[0][(0x1234 << 2) | 1] = 0xBE
        model.data[0][(0x1234 << 2) | 2] = 0xAD
        model.data[0][(0x1234 << 2) | 3] = 0xDE
        result = yield from wb_xfer(addr=0x0001234)
        assert result == 0xDEADBEEF, f"{result:08x}"

    def test_flash_quad_read():
        yield from _cfg_quad()
        for i in range(8):
            model.data[0][(0x1234 << 2) + i] = i + 0x51
        result = yield from wb_xfer(addr=0x0001234)
        assert result == 0x54535251, f"{result:08x}"

    def test_flash_quad_read_continue():
        yield from _cfg_quad()
        for i in range(8):
            model.data[0][(0x1234 << 2) + i] = i + 0x51
        init_xfers = model.xfer_count
        result = yield from wb_xfer(addr=0x0001234)
        assert result == 0x54535251, f"{result:08x}"
        result = yield from wb_xfer(addr=0x0001235)
        assert result == 0x58575655, f"{result:08x}"
        assert model.xfer_count == init_xfers + 1 # assert kept alive


    def test_flash_quad_read_discontinue():
        yield from _cfg_quad()
        for i in range(4):
            model.data[0][(0x01234 << 2) + i] = i + 0x51
            model.data[0][(0x01237 << 2) + i] = i + 0x31
            model.data[0][(0x11237 << 2) + i] = i + 0x91
        init_xfers = model.xfer_count
        result = yield from wb_xfer(addr=0x0001234)
        assert result == 0x54535251, f"{result:08x}"
        result = yield from wb_xfer(addr=0x0001237)
        assert result == 0x34333231, f"{result:08x}"
        result = yield from wb_xfer(addr=0x0011237)
        assert result == 0x94939291, f"{result:08x}"
        assert model.xfer_count == init_xfers + 3 # assert not kept alive

    def test_ram_quad_read():
        yield from _cfg_quad()
        for i in range(12):
            model.data[1][(0xa5a5 << 2) + i] = i + 0x51
        result = yield from wb_xfer(addr=0x220a5a5)
        assert result == 0x54535251, f"{result:08x}"
        result = yield from wb_xfer(addr=0x220a5a6)
        assert result == 0x58575655, f"{result:08x}"
        result = yield from wb_xfer(addr=0x220a5a7)
        assert result == 0x5c5b5a59, f"{result:08x}"

    def _ram_word(dev, addr):
        return int.from_bytes(model.data[dev][(addr<<2):((addr+1)<<2)], byteorder="little")

    def test_ram_spi_write():
        yield from _cfg_spi()
        yield from wb_xfer(addr=0x2201234, write_data=0xca7f100f, write_sel=0b1111)
        assert _ram_word(1, 0x1234) == 0xca7f100f, f"{_ram_word(1, 0x1234):08x}"

    def test_ram_spi_write_sel():
        yield from _cfg_spi()
        for i in range(8):
            model.data[1][(0x01234 << 2) + i] = 0xff
        yield from wb_xfer(addr=0x2201234, write_data=0xBA000000, write_sel=0b1000)
        assert _ram_word(1, 0x1234) == 0xBAFFFFFF, f"{_ram_word(1, 0x1234):08x}"
        yield from wb_xfer(addr=0x2201234, write_data=0x00DC0000, write_sel=0b0100)
        assert _ram_word(1, 0x1234) == 0xBADCFFFF, f"{_ram_word(1, 0x1234):08x}"
        yield from wb_xfer(addr=0x2201235, write_data=0x0000A77E, write_sel=0b0011)
        assert _ram_word(1, 0x1235) == 0xFFFFA77E, f"{_ram_word(1, 0x1235):08x}"
        yield from wb_xfer(addr=0x2201235, write_data=0xBADC0000, write_sel=0b1100)
        assert _ram_word(1, 0x1235) == 0xBADCA77E, f"{_ram_word(1, 0x1235):08x}"

    def test_ram_quad_write():
        yield from _cfg_quad()
        yield from wb_xfer(addr=0x2401230, write_data=0xFEEDACA7, write_sel=0b1111)
        assert _ram_word(2, 0x1230) == 0xFEEDACA7, f"{_ram_word(2, 0x1230):08x}"

    def test_ram_quad_write_continue():
        yield from _cfg_quad()
        init_xfers = model.xfer_count
        yield from wb_xfer(addr=0x2201240, write_data=0x12345678, write_sel=0b1111)
        assert _ram_word(1, 0x1240) == 0x12345678, f"{_ram_word(1, 0x1240):08x}"
        yield from wb_xfer(addr=0x2201241, write_data=0x2468aabb, write_sel=0b1111)
        assert _ram_word(1, 0x1241) == 0x2468aabb, f"{_ram_word(1, 0x1241):08x}"
        assert model.xfer_count == init_xfers + 1 # assert kept alive


    def test_ram_max_burst():
        yield from _cfg_quad()
        init_xfers = model.xfer_count
        for i in range(31*4):
            model.data[1][(0x1000 << 2) + i] = i
        for i in range(31):
            yield from wb_xfer(addr=(0x2201000+i))
        assert model.xfer_count == init_xfers + 2 # assert kept alive

    tests = [v for k, v in locals().items() if k.startswith("test_")]

    failures = 0
    for test in tests:
        test_name = test.__name__
        print(f"Running {test_name}...")
        try:
            sim = Simulator(m)
            sim.add_clock(1e-6)
            def stimulus_process():
                yield from test()
            def model_process():
                yield Passive()
                yield Delay(0.25e-6)
                while True:
                    yield spi.d_i.eq(model.tick((yield spi.clk_o), (yield spi.cs_o), (yield spi.d_o)))
                    yield Delay(0.5e-6)
            sim.add_sync_process(stimulus_process)
            sim.add_process(model_process)
            with sim.write_vcd(f"test_results/qspi_{test_name}.vcd", f"test_results/qspi_{test_name}.gtkw"):
                sim.run()
        except Exception:
            traceback.print_exc()
            failures += 1
    sys.exit(0 if failures == 0 else 1)
if __name__ == '__main__':
    run_tests()
