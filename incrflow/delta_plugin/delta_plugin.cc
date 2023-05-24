#include "kernel/yosys.h"
#include "kernel/modtools.h"

#include <queue>

USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN


struct ModuleDeltaWorker {
	ModuleDeltaWorker(Design *curr_des, Design *base_des, Module *curr_mod, Module *base_mod) :
		curr_des(curr_des), base_des(base_des), curr_mod(curr_mod), base_mod(base_mod),
		currwalker(curr_des, curr_mod), base_walker(curr_des, base_mod) {};

	Design *curr_des, *base_des;
	Module *curr_mod, *base_mod;
	ModWalker currwalker, base_walker;
	dict<SigBit, SigBit> matched_bits;
	dict<IdString, IdString> matched_cells;

	std::queue<std::pair<SigBit, SigBit>> equiv_visit;
	void run()
	{
		// Seed with primary outputs (TODO: also seed with submodule instance inputs)
		for (Wire *wire : curr_mod->wires()) {
			if (!wire->port_output)
				continue;
			if (!base_mod->wire(wire->name))
				continue;
			Wire *base_wire = base_mod->wire(wire->name);
			// TODO: aliases, constant outputs, etc etc
			for (int i = 0; i < GetSize(wire); i++) {
				if (i >= GetSize(base_wire))
					break;
				equiv_visit.emplace(SigBit(wire, i), SigBit(base_wire, i));
			}
		}
	} 
};

struct IncrDeltaPass : public Pass
{
	IncrDeltaPass() : Pass("incr_delta") { }

	void execute(vector<string>, Design *design) override
	{
		// Structural equivalence check that aims to find the differences between two designs for incremental compilation
		Design *base = saved_designs.at("base");
		ModuleDeltaWorker worker(design, base, design->module("top"), base->module("top"));
		worker.run();
	}
} IncrDeltaPass;

PRIVATE_NAMESPACE_END
