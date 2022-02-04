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

    top.step();
    auto tick = [&]() {
        top.p_clk.set(false);
        top.step();
        top.p_clk.set(true);
        top.step();
        trace.tick();
    };
    top.p_rst.set(true);
    tick();
    top.p_rst.set(false);

    while (1) {
        tick();
    }
    return 0;
}
