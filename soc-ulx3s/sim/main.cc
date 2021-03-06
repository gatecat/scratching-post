#undef NDEBUG

#include <backends/cxxrtl/cxxrtl.h>
#include "build/sim_soc.h"
#include "models/spiflash.h"
#include "models/wb_mon.h"

#include "models/log.h"

#include <fstream>

using namespace cxxrtl_design;

int main(int argc, char **argv) {
    cxxrtl_design::p_sim__top top;

    wb_mon_set_output(*top.cell_p_bus__mon, "build/wishbone_log.csv");
    spiflash_load(*top.cell_p_flash, "../../vex-soc/software/bios.bin", 0x00100000U);

    spiflash_load(*top.cell_p_flash, "../../vex-soc/linux/linux.dtb", 15*1024*1024 + 512*1024);
    spiflash_load(*top.cell_p_flash, "../../../linux/arch/riscv/boot/xipImage", 8*1024*1024);
    spiflash_load(*top.cell_p_flash, "../../../rootfs.bin", 2*1024*1024);


    top.step();
    auto tick = [&]() {
        top.p_clk.set(false);
        top.step();
        top.p_clk.set(true);
        top.step();
    };
    top.p_rst.set(true);
    tick();
    top.p_rst.set(false);

    while (1) {
        tick();
    }
    return 0;
}
