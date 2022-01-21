#undef NDEBUG

#include <backends/cxxrtl/cxxrtl.h>
#include <backends/cxxrtl/cxxrtl_vcd.h>
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

    cxxrtl::debug_items all_debug_items;
    top.debug_info(all_debug_items);

    cxxrtl::vcd_writer vcd;
    vcd.timescale(1, "us");

    vcd.add_without_memories(all_debug_items);
    std::ofstream trace_vcd("build/trace.vcd");

	load_memory(top.memory_p_soc_2e_sim__rom_2e___mem, "../software/bios.bin", 1*1024*1024);
	load_memory(top.memory_p_soc_2e_sim__rom_2e___mem, "../linux/linux.dtb", 1*1024*1024 + 512*1024);
	load_memory(top.memory_p_soc_2e_sim__rom_2e___mem, "/home/gatecat/linux/arch/riscv/boot/xipImage", 8*1024*1024);

	wb_mon_set_output(*top.cell_p_bus__mon_2e_bb, "build/wishbone_log.csv");

	ExecTrace trace("build/cpu.trace", top.p_soc_2e_cpu_2e_vex_2e_decode__to__execute__PC); 

	top.step();
	int64_t i = 0, vcd_count = 0;
	bool enable_vcd = false;
	auto tick = [&]() {
		top.p_clk.set(false);
		top.step();
		if (enable_vcd)
			vcd.sample(i*2 + 0);
		top.p_clk.set(true);
		top.step();
		if (enable_vcd)
			vcd.sample(i*2 + 1);
		trace.tick();
		/*if (((i++) % 500000) == 0) {
			log("scause: %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__scause__exceptionCode.get<uint32_t>());
			log("mcause: %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__mcause__exceptionCode.get<uint32_t>());
			log("sepc:   %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__sepc.get<uint32_t>());
			log("mepc:   %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__mepc.get<uint32_t>());
			log("stval:  %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__stval.get<uint32_t>());
			log("mtval:  %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__mtval.get<uint32_t>());
			log("stval:  %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__stval.get<uint32_t>());
			log("mtvec:  %d %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__mtvec__mode.get<uint32_t>(), top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__mtvec__base.get<uint32_t>());
			log("stvec:  %d %08x\n", top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__stvec__mode.get<uint32_t>(), top.p_soc_2e_cpu_2e_vex_2e_CsrPlugin__stvec__base.get<uint32_t>());
		}*/
		/*if (top.p_soc_2e_cpu_2e_vex_2e_decode__to__execute__PC.get<uint32_t>() == 0xc00221d4 && !enable_vcd) {
			log("enabling VCD trace!!\n");
			enable_vcd = true;
			vcd.sample(i*2 + 1);
		}*/
		if (enable_vcd) {
	        trace_vcd << vcd.buffer;
	        vcd.buffer.clear();
	        if ((i % 100) == 0)
	        	trace_vcd.flush();
	        ++vcd_count;
		}
	};
	top.p_rst.set(true);
	tick();
	top.p_rst.set(false);

	while (1) {
		tick();
		if (enable_vcd && vcd_count == 5000) {
			break;
		}
	}
	return 0;
}
