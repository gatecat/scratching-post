from module_gen import *

"""
Generate a complex DFF primitive
"""
def gen_dff(name, *,
	has_sr=False, has_en=False,
	gate_sr=False, gate_en=False,
	has_async=False,
	has_init=False, config_init=False,
	en_over_sr=False):
	m = ModuleGen(name, inputs=[ModulePort("CLK"), ModulePort("D")], outputs=[ModulePort("Q")])
	# optional control inputs
	if has_sr:
		m.add_input("SR")
		if gate_sr:
			m.add_prim("clb_and", a="SR", b=m.cfg("SR_USED"), x="sr_gate")
		else:
			m.add_assign("sr_gate", "SR")
	if has_en:
		m.add_input("EN")
		if gate_en:
			m.add_prim("clb_and", a="EN", b=m.cfg("EN_USED"), x="en_gate")
		else:
			m.add_assign("en_gate", "EN")
	if has_init:
		m.add_input("GSRN")

	if has_sr:
		s_nr = m.cfg("SET_NORESET")
		if has_async:
			sr_a = m.cfg("SR_ASYNC")

	sync_d = "D"
	# handle different EN/SR priorities
	if not en_over_sr and has_en:
		# EN gates SR
		m.add_prim("clb_mux2", a0="Q", a1=sync_d, s0="en_gate", x="d_ce")
		sync_d = "d_ce"
	if has_sr:
		# synchronous set/reset
		if has_async:
			m.add_prim("clb_andnot", a="sr_gate", b=sr_a, x="sr_sync")
		else:
			m.add_assign("sr_sync", "sr_gate")
		m.add_prim("clb_mux2", a0=sync_d, a1=s_nr, s0="sr_sync", x="d_sr")
		sync_d = "d_sr"
	if en_over_sr and has_en:
		m.add_prim("clb_mux2", a0="Q", a1=sync_d, s0="en_gate", x="d_sren")
		sync_d = "d_sren"
	if has_async:
		m.add_prim("clb_and", a="sr_gate", b=sr_a, x="sr_async")
		sr_async = "sr_async"
		if has_init and not config_init:
			# INIT not separately configurable; implement just by pulsing the async SR
			m.add_prim("clb_ornot", a="sr_async", b="GSRN", x="sr_async_i")
			sr_async = "sr_async_i"
		m.add_prim("clb_not", a=s_nr, x="ns_r")
		m.add_prim("clb_nand", a=sr_async, b="ns_r", x="sr_rn")
		m.add_prim("clb_nand", a=sr_async, b=s_nr, x="sr_sn")
		rn = "sr_rn"
		sn = "sr_sn"
	if has_init and (config_init or not has_sr):
		# INIT separately configurable (or no SR present), have to generate logic to route it
		init = m.cfg("INIT")
		m.add_prim("clb_or", a="GSRN", b=init, x="init_rn")
		m.add_prim("clb_ornot", a="GSRN", b=init, x="init_sn")
		if has_sr:
			m.add_prim("clb_and", a=rn, b="init_rn", x="rn")
			m.add_prim("clb_and", a=sn, b="init_sn", x="sn")
			rn = "rn"
			sn = "sn"
		else:
			rn = "init_rn"
			sn = "init_sn"
	# finally, the DFF itself
	if has_async or has_init:
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
	m = gen_dff(name, **cfg)
	m.finalise(out_file, append_cfg=True)
