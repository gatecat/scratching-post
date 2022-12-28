# Used to specify that a signal is a configurable mux rather than a fixed connection
class CMux:
	def __init__(self, name, *inputs):
		self.name = name
		self.inputs = list(inputs)

def get_sig(m, sig):
	from module_utils import add_cfgmux
	if isinstance(CMux, sig):
		out = f"{sig.name}"
		add_cfgmux(m, f"mux_{sig.name}", out, [get_sig(m, i) for i in sig.inputs])
		return out
	else:
		return sig
