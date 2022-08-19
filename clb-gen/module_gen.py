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
		self.config_tags = []

	def add_input(self, name, width=1):
		self.inputs.append(ModulePort(name, width))

	def add_output(self, name, width=1):
		self.outputs.append(ModulePort(name, width))

	def add_assign(self, dst, src):
		self.assigns += [(dst, src)]

	def cfg(self, name):
		idx = len(self.config_bits)
		self.config_bits.append(name)
		return f"cfg[{idx}]"
			
	def cfg(self, name, width):
		idx = len(self.config_bits)
		for i in range(width):
			self.config_bits.append(f"{name}[{i}]")
		return list(f"cfg[{idx+i}]" for i in range(width))

	def add_tag(self, name, cbits):
		bits = []
		for bit in cbits:
			if bit.startswith("cfg["):
				bits.append(int(bit[4:-1]))
			else:
				bits.append(bit)
		self.config_tags.append(tuple([name, ] + bits))
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
			for m, bits in mod.config_tags:
				self.config_tags.append(tuple([f"{name}.{b}", ] + [b + cfg_start for b in bits]))
			ports["cfg"] = f"cfg[{cfg_start+len(mod.config_bits)-1}:{cfg_start}]"
		self.insts.append(Instance(name, mod.module_name, ports))
	def finalise(self, filename, append_cfg=False):
		with open(filename, "w") as f:
			print(f"module {self.module_name} (", file=f)
			ports = []
			# signals for which we don't need to create a wire
			known_sigs = set()
			# write ports
			for i in self.inputs:
				ports.append(f"\tinput wire [{i.width-1}:0] {i.name}" if i.width > 1 else f"\tinput wire {i.name}")
				known_sigs.add(i.name)
			if len(self.config_bits) > 0:
				ports.append(f"\tinput wire [{len(self.config_bits)-1}:0] cfg")
				known_sigs.add("cfg")
			for o in self.outputs:
				ports.append(f"\toutput wire [{o.width-1}:0] {o.name}" if o.width > 1 else f"\toutput wire {o.name}")
				known_sigs.add(o.name)
			# use join() to avoid trailing comma issues
			print(",\n".join(ports), file=f)
			print(");", file=f)
			# auto determine signals
			sigs = set()
			for inst in self.insts:
				for sig in inst.ports.values():
					s = sig.split('[')[0]
					if s not in known_sigs:
						sigs.add(s)
			for pair in self.assigns:
				for sig in pair:
					s = sig.split('[')[0]
					if s not in known_sigs:
						sigs.add(s)
			# write list of wires
			for s in sorted(sigs):
				print(f"\twire {s};", file=f)
			print("", file=f)
			# write instances
			for inst in self.insts:
				print(f"\t{inst.typ} {inst.name} ({', '.join(f'.{k}({v})' for k, v in sorted(inst.ports.items(), key=lambda x:x[0]))});", file=f)
			# write assigns
			if len(self.assigns) > 0:
				print("", file=f)
				for dst, src in self.assigns:
					print(f"\tassign {dst} = {src};", file=f)
			print("endmodule", file=f)
			if append_cfg:
				print("/** CONFIG **", file=f)
				for i, b in enumerate(self.config_bits):
					print(f"  {i:>4d} {b}", file=f)
				print("**/", file=f)
				print("/** TAGS **", file=f)
				for t in enumerate(self.config_tags):
					print(f"  {t[0]} {' '.join(str(b) for b in t[1:])}", file=f)
				print("**/", file=f)
