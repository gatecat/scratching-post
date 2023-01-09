from module_gen import *

@dataclass
class LUTTap:
	name: str
	level: int # the layer in the multiplexer tree (K is the final output)
	index: int # the offset from the LSB of the layer

"""
Generate a mux tree structure, with a set of intermediate taps
 extra_taps is used for extra intermediate outputs for fracturable LUTs
"""
def gen_lut(name, k, extra_taps=[], with_lutram=False):
	taps = extra_taps + [LUTTap("O", k, 0), ]
	inputs = [ModulePort("I", k)]
	if with_lutram:
		# TODO decoded or undecoded write address/strobe?
		inputs += [ModulePort("CFG_MODE"), ModulePort("WR_STROBE", 2**k), ModulePort("WR_DATA")]
	m = ModuleGen(name, inputs=inputs, outputs=[ModulePort(t.name, 1) for t in taps])
	if with_lutram:
		m.gen_cfg_storage = True
	level = 0
	if with_lutram:
		cfg_bits = m.cfg_word(f"INIT", 2**k, ext_memory=True)
		for i in range(2**k):
			cfg_strobe, cfg_data = cfg_bits[i]
			# these muxes are expensive - but should mostly be optimised out if a "long and thin" design with lots of frames and not many bits...
			m.add_prim(f"clb_mux2", f"wr_dmux{i}",
				x=f"lut_d_muxed{i}",
				a0=f"WR_DATA", a1=cfg_data,
				s0="CFG_MODE"
			)
			m.add_prim(f"clb_or", f"wr_strbor{i}",
				x=f"lut_wr_strobe{i}",
				a=f"WR_STROBE[{i}]", b=cfg_strobe,
			)
			m.add_prim(f"cfg_latch", f"lut_latch{i}",
				d=f"lut_d_muxed{i}", en=f"lut_wr_strobe{i}", q=f"lut_data{i}")
		layer = [f"lut_data{i}" for i in range(2**k)]
	else:
		# plain fixed init
		layer = m.cfg_word(f"INIT", 2**k)
	while True:
		can_mux4 = True
		for t in taps:
			# taps for this layer
			if t.level == level:
				m.add_assign(t.name, layer[t.index])
			# check if it's safe to generate a MUX4 as we have no taps the next level
			if t.level == level+1:
				can_mux4 = False
		if level == k:
			# done
			assert len(layer) == 1
			break
		layer_size = 2 if can_mux4 else 1
		mux_size = 2**layer_size
		next_width = len(layer) // mux_size
		next_layer = [f"l{level+layer_size}_{i}" for i in range(next_width)]
		for i in range(next_width):
			m.add_prim(f"clb_mux{mux_size}", f"l{level}_imux{i}",
				x=next_layer[i],
				**{f"a{j}": layer[mux_size*i + j] for j in range(mux_size)},
				**{f"s{j}": f"I[{level+j}]" for j in range(layer_size)},
			)
		layer = next_layer
		level += layer_size
	return m

if __name__ == '__main__':
	import sys
	out_file = sys.argv[1]
	k = int(sys.argv[2])
	name = f"CLB_LUT{k}"
	extra_taps = []
	for arg in sys.argv[3:]:
		s = arg.split(":")
		extra_taps.append(LUTTap(s[0], int(s[1]), int(s[2])))
	m = gen_lut(name, k, extra_taps, with_lutram=True)
	with open(out_file, "w") as f:
		m.finalise(f)

