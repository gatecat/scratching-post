#include <backends/cxxrtl/cxxrtl.h>
#include "build/sim_soc.h"
#include "models/spiflash.h"
#include "models/wb_mon.h"

#include "models/log.h"

#include <fstream>

using namespace cxxrtl_design;

struct ExecTrace {
	ExecTrace(const std::string &filename, wire<32> &signal, wire<32> &instr) : out(filename), signal(signal), instr(instr) {};
	std::ofstream out;
	wire<32> &signal, &instr;
	uint32_t last = 0xFFFFFFFF;
	void tick() {
		uint32_t pc = signal.get<uint32_t>();
		if (pc != last)
			out << stringf("%08x %08x", pc, instr.get<uint32_t>()) << std::endl;
		last = pc;
	}
};

int main(int argc, char **argv) {
	cxxrtl_design::p_sim__top top;

	spiflash_load(*top.cell_p_spiflash_2e_bb, "../software/bios.bin", 1*1024*1024);
	spiflash_load(*top.cell_p_spiflash_2e_bb, "../linux/linux.dtb", 1*1024*1024 + 512*1024);
	spiflash_load(*top.cell_p_spiflash_2e_bb, "/home/gatecat/linux/arch/riscv/boot/Image", 2*1024*1024);

	wb_mon_set_output(*top.cell_p_bus__mon_2e_bb, "build/wishbone_log.csv");

	ExecTrace trace("build/cpu.trace", top.p_soc_2e_cpu_2e_vex_2e_memory__to__writeBack__PC, top.p_soc_2e_cpu_2e_vex_2e_memory__to__writeBack__INSTRUCTION);

	std::ifstream kernel("/home/gatecat/linux/arch/riscv/boot/Image", std::ios::binary);
	uint32_t addr = (1*1024*1024)/4 - 1;
	top.memory_p_soc_2e_hyperram0_2e___mem[addr++].set(0xdeadbeef); // magic
	while (kernel) {
		uint32_t word = 0;
		kernel.read(reinterpret_cast<char*>(&word), 4);
		if (!kernel)
			break;
		top.memory_p_soc_2e_hyperram0_2e___mem[addr++].set(word);
	}
	// memory_p_soc_2e_hyperram0_2e___mem

	top.step();
	int i = 0;
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
