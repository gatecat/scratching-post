#undef NDEBUG

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

void load_memory(memory<32> &mem, const std::string &filename, uint32_t offset) {
	assert((offset % 4) == 0);
	offset /= 4;
	std::ifstream in(filename, std::ios::binary);
	while (true) {
		uint8_t word[4];
		in.read(reinterpret_cast<char*>(&word), 4);
		if (!in)
			break;
		mem[offset++].set<uint32_t>(
			uint32_t(word[3]) << 24U |
			uint32_t(word[2]) << 16U |
			uint32_t(word[1]) <<  8U |
			uint32_t(word[0]));
	}
}

int main(int argc, char **argv) {
	cxxrtl_design::p_sim__top top;

	load_memory(top.memory_p_soc_2e_sim__rom_2e___mem, "../software/bios.bin", 1*1024*1024);
	load_memory(top.memory_p_soc_2e_sim__rom_2e___mem, "../linux/linux.dtb", 1*1024*1024 + 512*1024);
	load_memory(top.memory_p_soc_2e_sim__rom_2e___mem, "/home/gatecat/linux/arch/riscv/boot/xipImage", 8*1024*1024);

	wb_mon_set_output(*top.cell_p_bus__mon_2e_bb, "build/wishbone_log.csv");

	ExecTrace trace("build/cpu.trace", top.p_soc_2e_cpu_2e_vex_2e_decode__to__execute__PC);

	// 

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
