import sys
from pathlib import Path

from amaranth import *
from amaranth.sim import Simulator, Delay, Settle

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
            yield spi.d_i.eq(model.tick((yield spi.clk_o), (yield spi.cs_o), (yield spi.d_o)))
            if (yield spi.data_bus.ack):
                result = yield spi.data_bus.dat_w
                yield spi.data_bus.stb.eq(0)
                yield spi.data_bus.cyc.eq(0)
                yield
                break
            yield
        return result

    def test_flash_spi_read():
        model.data[0][(0x1234 << 2) | 0] = 0xEF
        model.data[0][(0x1234 << 2) | 1] = 0xBE
        model.data[0][(0x1234 << 2) | 2] = 0xAD
        model.data[0][(0x1234 << 2) | 3] = 0xDE
        result = yield from wb_xfer(addr=0x0001234)
        assert result == 0xDEADBEEF, f"{result:08x}"

    tests = [v for k, v in locals().items() if k.startswith("test_")]

    failures = 0
    for test in tests:
        test_name = test.__name__
        print(f"Running {test_name}...")
        try:
            sim = Simulator(m)
            sim.add_clock(1e-6)
            def process():
                yield from test()
            sim.add_sync_process(process)
            with sim.write_vcd(f"test_results/qspi_{test_name}.vcd", f"test_results/qspi_{test_name}.gtkw"):
                sim.run()
        except Exception:
            traceback.print_exc()
            failures += 1
    sys.exit(0 if failures == 0 else 1)
if __name__ == '__main__':
    run_tests()
