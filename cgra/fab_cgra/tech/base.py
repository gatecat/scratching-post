from amaranth import *

class BaseTech:
	def __init__(self, m):
		self.m = m
		self.autoidx = 0

	def _add_submod(self, name, inst):
		if name is None:
			name = f'i{self.autoidx}'
			self.autoidx += 1
		assert not hasattr(self.submodules, name)
		setattr(self.submodules, name, inst)

	def add_gate(self, type, name=None, **ports):
		inst = Instance(typ,
			**{f'{"o" if p in ("x", "y", "q") else "i"}_{p}': q for p, q in ports}
		)
		self._add_submod(name, inst)




