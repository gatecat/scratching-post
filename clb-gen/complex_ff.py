from module_gen import *
from module_config import *

@dataclass
class FFConfig:
	name: str
	data: str|CMux = "D"
	q: str = "Q"
	clk: str|CMux = "CLK"
	sr: str|CMux|None = None
	en: str|CMux|None = None
	gate_sr: bool = False
	gate_en: bool = False
	has_async: bool = False
	has_init: bool = False
	config_init: bool = False
	en_over_sr: bool = False

"""
Generate a complex DFF primitive
"""
def gen_dff(name, cfg):
	m = ModuleGen(name, inputs=[ModulePort("CLK"), ModulePort("D")], outputs=[ModulePort("Q")])
	# optional control inputs
	if cfg.sr is not None:
		m.add_input("SR")
		if cfg.gate_sr:
			m.add_prim("clb_and", a="SR", b=m.cfg("SR_USED"), x="sr_gate")
		else:
			m.add_assign("sr_gate", "SR")
	if cfg.en is not None:
		m.add_input("EN")
		if cfg.gate_en:
			m.add_prim("clb_and", a="EN", b=m.cfg("EN_USED"), x="en_gate")
		else:
			m.add_assign("en_gate", "EN")
	if cfg.has_init:
		m.add_input("GSRN")

	if cfg.sr is not None:
		s_nr = m.cfg("SET_NORESET")
		if cfg.has_async:
			sr_a = m.cfg("SR_ASYNC")

	sync_d = "D"
	# handle different EN/SR priorities
	if not cfg.en_over_sr and cfg.en is not None:
		# EN gates SR
		m.add_prim("clb_mux2", a0="Q", a1=sync_d, s0="en_gate", x="d_ce")
		sync_d = "d_ce"
	if cfg.sr is not None:
		# synchronous set/reset
		if cfg.has_async:
			m.add_prim("clb_andnot", a="sr_gate", b=sr_a, x="sr_sync")
		else:
			m.add_assign("sr_sync", "sr_gate")
		m.add_prim("clb_mux2", a0=sync_d, a1=s_nr, s0="sr_sync", x="d_sr")
		sync_d = "d_sr"
	if cfg.en_over_sr and cfg.en is not None:
		m.add_prim("clb_mux2", a0="Q", a1=sync_d, s0="en_gate", x="d_sren")
		sync_d = "d_sren"
	if cfg.has_async:
		m.add_prim("clb_and", a="sr_gate", b=sr_a, x="sr_async")
		sr_async = "sr_async"
		if cfg.has_init and not cfg.config_init:
			# INIT not separately configurable; implement just by pulsing the async SR
			m.add_prim("clb_ornot", a="sr_async", b="GSRN", x="sr_async_i")
			sr_async = "sr_async_i"
		m.add_prim("clb_not", a=s_nr, x="ns_r")
		m.add_prim("clb_nand", a=sr_async, b="ns_r", x="sr_rn")
		m.add_prim("clb_nand", a=sr_async, b=s_nr, x="sr_sn")
		rn = "sr_rn"
		sn = "sr_sn"
	if cfg.has_init and (cfg.config_init or cfg.sr is None):
		# INIT separately configurable (or no SR present), have to generate logic to route it
		init = m.cfg("INIT")
		m.add_prim("clb_or", a="GSRN", b=init, x="init_rn")
		m.add_prim("clb_ornot", a="GSRN", b=init, x="init_sn")
		if cfg.sr is not None and cfg.has_async:
			m.add_prim("clb_and", a=rn, b="init_rn", x="rn")
			m.add_prim("clb_and", a=sn, b="init_sn", x="sn")
			rn = "rn"
			sn = "sn"
		else:
			rn = "init_rn"
			sn = "init_sn"
	# finally, the DFF itself
	if cfg.has_async or (cfg.has_init and (cfg.config_init or cfg.sr is None)):
		m.add_prim("clb_dffrs", clk="CLK", d=sync_d, rn=rn, sn=sn, q="Q")
	else:
		m.add_prim("clb_dff", clk="CLK", d=sync_d, q="Q")
	return m

if __name__ == '__main__':
	import sys
	out_file = sys.argv[1]
	name = f"CLB_DFF"
	cfg = {}
	for arg in sys.argv[2:]:
		s = arg.split('=')
		cfg[s[0]] = True if len(s) == 1 else s[1]
	m = gen_dff(name, FFConfig(data="D", **cfg))
	with open(out_file, "w") as f:
		m.finalise(out_file, append_cfg=True)
