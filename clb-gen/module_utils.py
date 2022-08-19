from module_gen import *

def add_cfgmux(m, name, output, inputs):
	# TODO: optimal mux tree generation
	n = len(inputs).bit_length()
	cfgbits = m.cfg(name, n)
	autoidx = 0
	def recursive_muxgen(sigs, bits, hot_bits):
		nonlocal autoidx
		print(bits)
		if len(sigs) == 1:
			# terminal case
			m.add_tag(f"{name}.{sigs[0]}", hot_bits)
			return sigs[0]
		else:
			mux_depth = 2 if len(sigs) > 2 else 1
			mux_size = 2**mux_depth
			# TODO: check this dividing is correct
			chunks = []
			chunk_start = 0
			for i in range(mux_size):
				chunk_end = (i + 1) * len(sigs) // mux_size
				chunk = sigs[chunk_start:chunk_end]
				if len(chunk) > 0:
					chunks.append(chunk)
				chunk_start = chunk_end
			# the recursive part
			for i in range(len(chunks)):
				autoidx += 1
				chunks[i] = recursive_muxgen(chunks[i], bits[:-mux_depth],
					hot_bits + list(bits[(len(bits) - mux_depth) + j] for j in range(mux_depth) if i & (1 << j)))
			# the mux part
			out_sig = f"{name}_n{autoidx}"
			m.add_prim(f"clb_mux{mux_size}",
				x=out_sig,
				**{f"a{j}": chunks[j] for j in range(len(chunks))},
				**{f"s{j}": bits[(len(bits) - mux_depth) + j] for j in range(mux_depth)},
			)
			return out_sig
	result = recursive_muxgen(inputs, cfgbits, [])
	m.add_assign(output, result)
if __name__ == '__main__':
	# crude test
	import sys
	if sys.argv[1] == "mux":
		k = int(sys.argv[2])
		inputs = [chr(ord('A') + i) for i in range(k)]

		m = ModuleGen(module_name="test_mux", inputs=[ModulePort(i) for i in inputs], outputs=[ModulePort("X")])
		add_cfgmux(m, "CFGMUX", "X", inputs)
		m.finalise(sys.argv[3], True)
	else:
		assert False, sys.argv[1]
