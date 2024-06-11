#include "kernel/yosys.h"
#include "kernel/sigtools.h"

USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN

struct SplitTriPass : public Pass
{
	SplitTriPass() : Pass("splittri") { }

	void execute(vector<string>, Design *design) override
	{
		RTLIL::Module *module = design->top_module();
		std::vector<RTLIL::Cell *> to_delete;

		for (auto cell : module->cells()) {
			if (cell->type != ID($tribuf))
				continue;
			log_assert(cell->getParam(ID::WIDTH) == 1); // TODO (fine for gate level)
			Wire *y = cell->getPort(ID::Y)[0].wire;
			if (!y || !y->port_output)
				continue;
			{
				Wire *out = module->addWire(IdString(stringf("%s.O", y->name.c_str())));
				module->connect(out, cell->getPort(ID::A));
				out->port_output = true;
			}

			{
				Wire *out_en = module->addWire(IdString(stringf("%s.OE", y->name.c_str())));
				module->connect(out_en, cell->getPort(ID::EN));
				out_en->port_output = true;
			}

			if (y->port_input) {
				Wire *in = module->addWire(IdString(stringf("%s.I", y->name.c_str())));
				module->connect(y, in);
				in->port_input = true;
			}

			y->port_output = false;
			y->port_input = false;
			to_delete.push_back(cell);
		}
		for (auto cell : to_delete) {
			module->remove(cell);
		}
		module->fixup_ports();
	}
} SplitTriPass;

PRIVATE_NAMESPACE_END