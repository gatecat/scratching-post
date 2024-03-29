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
		self.vecs = []
		self.inst_autoidx = 0
		self.sig_autoidx = 0
		self.gen_cfg_storage = False
		self.cfg_width = 32
		self.config_bits = []
		self.config_tags = []

	def add_input(self, name, width=1):
		self.inputs.append(ModulePort(name, width))

	def add_output(self, name, width=1):
		self.outputs.append(ModulePort(name, width))

	def add_vector_sig(self, name, width):
		self.vecs.append((name, width))

	def add_assign(self, dst, src):
		self.assigns += [(dst, src)]

	def cfg(self, name, ext_memory=False):
		if ext_memory:
			assert self.gen_cfg_storage, "getting raw config access requires gen_cfg_storage set"
		idx = len(self.config_bits)
		self.config_bits.append((name, ext_memory))
		if ext_memory:
			return (f"cfg_strobe[{idx//self.cfg_width}]", f"cfg_data[{idx%self.cfg_width}]")
		else:
			return f"cfg[{idx}]"

	def cfg_word(self, name, width, ext_memory=False):
		if ext_memory:
			assert self.gen_cfg_storage, "getting raw config access requires gen_cfg_storage set"
		idx = len(self.config_bits)
		for i in range(width):
			self.config_bits.append((f"{name}[{i}]", ext_memory))
		if ext_memory:
			return list((f"cfg_strobe[{(idx+i)//self.cfg_width}]", f"cfg_data[{(idx+i)%self.cfg_width}]") for i in range(width))
		else:
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

	def _cfg_height(self):
		bits = len(self.config_bits)
		return (bits + self.cfg_width - 1) // self.cfg_width

	def add_submod(self, mod, name=None, **kwargs):
		if name is None:
			name = self.autoinst()
		ports = dict(kwargs)
		# auto propagate cbits
		if len(mod.config_bits) > 0:
			if mod.gen_cfg_storage:
				# submodule must be aligned
				while len(self.config_bits) % self.cfg_width != 0:
					self.config_bits.append((f"__padding_{len(self.config_bits)}", True))
			cfg_start = len(self.config_bits)
			for b, _ in mod.config_bits:
				self.config_bits.append((f"{name}.{b}", mod.gen_cfg_storage))
			for m, bits in mod.config_tags:
				self.config_tags.append(tuple([f"{name}.{b}", ] + [b + cfg_start for b in bits]))
			if mod.gen_cfg_storage:
				# propagate data/strobe
				ports["cfg_strobe"] = f"cfg_strobe[{cfg_start//self.cfg_width+mod._cfg_height()-1}:{cfg_start//self.cfg_width}]"
				ports["cfg_data"] = f"cfg_data"
			else:
				ports["cfg"] = f"cfg[{cfg_start+len(mod.config_bits)-1}:{cfg_start}]"
		self.insts.append(Instance(name, mod.module_name, ports))
	def finalise(self, f, append_cfg=False):
		print(f"module {self.module_name} (", file=f)
		ports = []
		# signals for which we don't need to create a wire
		known_sigs = set()
		# write ports
		for i in self.inputs:
			ports.append(f"\tinput wire [{i.width-1}:0] {i.name}" if i.width > 1 else f"\tinput wire {i.name}")
			known_sigs.add(i.name)
		if len(self.config_bits) > 0:
			if self.gen_cfg_storage:
				ports.append(f"\tinput wire [{self.cfg_width-1}:0] cfg_data")
				ports.append(f"\tinput wire [{self._cfg_height()-1}:0] cfg_strobe")
				known_sigs.add("cfg_data")
				known_sigs.add("cfg_strobe")
			else:
				ports.append(f"\tinput wire [{len(self.config_bits)-1}:0] cfg")
				known_sigs.add("cfg")
		for o in self.outputs:
			ports.append(f"\toutput wire [{o.width-1}:0] {o.name}" if o.width > 1 else f"\toutput wire {o.name}")
			known_sigs.add(o.name)
		# use join() to avoid trailing comma issues
		print(",\n".join(ports), file=f)
		print(");", file=f)
		# generate config memory if needed
		if len(self.config_bits) > 0 and self.gen_cfg_storage:
			print(f"\twire [{len(self.config_bits)-1}:0] cfg;", file=f)
			for i, (name, ext_memory) in enumerate(self.config_bits):
				if ext_memory:
					continue
				print(f"\tcfg_latch cfg_mem_{i} (.d(cfg_data[{i%self.cfg_width}]), .en(cfg_strobe[{i//self.cfg_width}]), .q(cfg[{i}]));", file=f)
			print("", file=f)
			known_sigs.add("cfg")
		for vec, width in self.vecs:
			print(f"\twire [{width-1}:0] {vec};", file=f)
			known_sigs.add(vec)
		# auto determine signals
		def split_cat(sig):
			s = sig.strip()
			if s.startswith('{'):
				assert s.endswith('}'), s
				result = []
				for entry in s[1:-1].split(","):
					result += split_cat(entry)
				return result
			else:
				return [s.split('[')[0], ]
		sigs = set()
		for inst in self.insts:
			for key, sig in inst.ports.items():
				if key.startswith("param_"):
					continue
				for s in split_cat(sig):
					if s not in known_sigs:
						sigs.add(s)
		for pair in self.assigns:
			for sig in pair:
				for s in split_cat(sig):
					if s not in known_sigs:
						sigs.add(s)
		# write list of wires
		for s in sorted(sigs):
			print(f"\twire {s};", file=f)
		print("", file=f)
		# write instances
		for inst in self.insts:
			if any(k.startswith("param_") for k in inst.ports.keys()):
				params = f"#({', '.join(f'.{k[6:]}({v}) ' for k, v in sorted(inst.ports.items(), key=lambda x:x[0]) if k.startswith('param_'))})"
			else:
				params = ""
			ports = ', '.join(f'.{k}({v})' for k, v in sorted(inst.ports.items(), key=lambda x:x[0]) if not k.startswith("param_"))
			print(f"\t{inst.typ} {params}{inst.name} ({ports});", file=f)
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
