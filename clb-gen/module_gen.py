from dataclasses import dataclass

@dataclass
class ModulePort:
	name: str
	width: int = 1

@dataclass
class Instance:
	name: str
	typ: str
	ports: dict[str, str]

class ModuleGen:
	def __init__(self, module_name, inputs=[], outputs=[]):
		self.module_name = module_name
		self.inputs = list(inputs)
		self.outputs = list(outputs)
		self.assigns = []
		self.insts = []
		self.inst_autoidx = 0
		self.sig_autoidx = 0
		self.config_bits = []

	def add_input(self, name, width=1):
		self.inputs.append(ModulePort(name, width))

	def add_output(self, name, width=1):
		self.outputs.append(ModulePort(name, width))

	def add_assign(self, dst, src):
		self.assigns += [(dst, src)]

	def cfg(self, name, width=1):
		idx = len(self.config_bits)
		if width == 1:
			self.config_bits.append(name)
			return f"cfg[{idx}]"
		else:
			for i in range(width):
				self.config_bits.append(f"{name}[{i}]")
			return f"cfg[{idx+width-1}:{idx}]"

	def autosig(self):
		self.sig_autoidx += 1
		return f"n{self.sig_autoidx}"

	def autoinst(self):
		self.inst_autoidx += 1
		return f"i{self.inst_autoidx}"

	def add_prim(self, typ, name=None, **kwargs):
		if name is None:
			name = self.autoinst()
		self.insts.append(Instance(name, typ, dict(kwargs)))

	def add_submod(self, mod, name=None, **kwargs):
		if name is None:
			name = self.autoinst()
		ports = dict(kwargs)
		# auto propagate cbits
		if len(mod.config_bits) > 0:
			cfg_start = len(self.config_bits)
			for b in mod.config_bits:
				self.config_bits.append(f"{name}.{b}")
			ports["cfg"] = f"cfg[{cfg_start+len(mod.config_bits)-1}:{cfg_start}]"
		self.insts.append(Instance(name, mod.module_name, ports))
	def finalise(self, filename, append_cfg=False):
		with open(filename, "w") as f:
			print(f"module {self.module_name} (", file=f)
			ports = []
			known_sigs = set()
			for i in self.inputs:
				ports.append(f"\tinput wire [{i.width-1}:0] {i.name}" if i.width > 1 else f"\tinput wire {i.name}")
				known_sigs.add(i.name)
			if len(self.config_bits) > 0:
				ports.append(f"\tinput wire [{len(self.config_bits)-1}:0] cfg")
				known_sigs.add("cfg")
			for o in self.outputs:
				ports.append(f"\toutput wire [{o.width-1}:0] {o.name}" if o.width > 1 else f"\toutput wire {o.name}")
				known_sigs.add(o.name)
			print(",\n".join(ports), file=f)
			print(");", file=f)
			# auto determine signals
			sigs = set()
			for inst in self.insts:
				for sig in inst.ports.values():
					s = sig.split('[')[0]
					if s not in known_sigs:
						sigs.add(s)
			for s in sorted(sigs):
				print(f"\twire {s};", file=f)
			print("", file=f)
			for inst in self.insts:
				print(f"\t{inst.typ} {inst.name} ({', '.join(f'.{k}({v})' for k, v in sorted(inst.ports.items(), key=lambda x:x[0]))});", file=f)
			if len(self.assigns) > 0:
				print("", file=f)
				for dst, src in self.assigns:
					print(f"\tassign {dst} = {src};", file=f)
			print("endmodule", file=f)
			if append_cfg:
				print("/** CONFIG **", file=f)
				for i, b in enumerate(config_bits):
					print(f"  {i:>4d} {b}", file=f)
				print("**/", file=f)