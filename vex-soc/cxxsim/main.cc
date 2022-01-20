#include <backends/cxxrtl/cxxrtl.h>
#include "build/sim_soc.h"
#include "models/spiflash.h"
#include "models/wb_mon.h"

#include "models/log.h"

#include <fstream>

using namespace cxxrtl_design;

struct ExecTrace {
	ExecTrace(const std::string &filename, wire<32> &signal) : out(filename), signal(signal) {};
	std::ofstream out;
	wire<32> &signal;
	uint32_t last = 0xFFFFFFFF;
	void tick() {
		uint32_t pc = signal.get<uint32_t>();
		if (pc != last)
			out << stringf("%08x", pc) << std::endl;
		last = pc;
	}
};

int main(int argc, char **argv) {
	cxxrtl_design::p_sim__top top;

	spiflash_load(*top.cell_p_spiflash_2e_bb, "../software/bios.bin", 1*1024*1024);
	spiflash_load(*top.cell_p_spiflash_2e_bb, "../linux/linux.dtb", 1*1024*1024 + 512*1024);
	spiflash_load(*top.cell_p_spiflash_2e_bb, "/home/gatecat/linux/arch/riscv/boot/xipImage", 8*1024*1024);

	wb_mon_set_output(*top.cell_p_bus__mon_2e_bb, "build/wishbone_log.csv");

	ExecTrace trace("build/cpu.trace", top.p_soc_2e_cpu_2e_vex_2e_decode__to__execute__PC);

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
