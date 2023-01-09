from module_gen import *
from complex_ff import FFConfig, gen_dff
from lut_muxtree import LUTTap, gen_lut
from module_config import *

from dataclasses import dataclass, field

@dataclass
class GlbControl:
	name: str
	can_invert: bool = False

@dataclass
class LUTRamConfig:
	wr_data: str|CMux

@dataclass
class LUTRamControl:
	wr_clock: str|CMux
	wr_en : str|CMux
	wr_addr: list[str]


@dataclass
class CLBConfig:
	num_lcs: int = 8
	lut_k: int = 4
	extra_lut_taps: list[LUTTap] = field(default_factory=list)
	extra_inputs: list[str] = field(default_factory=list)
	lutram_lcs: dict[int, LUTRamConfig] = field(default_factory=dict)
	lutram_ctrl: LUTRamControl|None = None
	flipflops: list[FFConfig] = field(default_factory=list)
	# TODO: carry
	glb_ctrl: list[GlbControl] = field(default_factory=list)
	outputs: list[(str, str|CMux)] = field(default_factory=list)

def _generate_lc(cfg: CLBConfig, m: ModuleGen, f, index):
	lc = chr(ord('A') + index)
	print(f"// Submodules for LC {lc}", file=f)
	lut_inputs = [f"{lc}_I{i}" for i in range(cfg.lut_k)]
	extra_inputs = [f"{lc}_{x}" for x in cfg.extra_inputs]

	# generate LUT (TODO not a LUT or complex LUT)
	lut = gen_lut(f"{lc}_LUT", k, cfg.extra_lut_taps, with_lutram=index in cfg.lutram_lcs)
	ports = dict(
		I=f"{{{', '.join(reversed(lut_inputs))}}}",
		O=f"{lc}_LUT_O",
	)
	for tap in extra_lut_taps:
		ports[tap.name] = f"{lc}_{tap.name}"
	if index in cfg.lutram_lcs:
		ports["CFG_MODE"] = "CFG_MODE"
		ports["WR_STROBE"] = "lutram_wr_strobe"
		ports["WR_DATA"] = get_sig(m, cfg, cfg.lutram_lcs[index].wr_data, prefix=f"{lc}_")
	m.add_submod(lut, f"{lc}_LUT_i", **ports)
	lut.finalise(f)
	# TODO: carry
	# TODO: configuring bit/frame aspect ratio 
	# generate FFs
	for ff in cfg.flipflops:
		ff = gen_dff(f"{lc}_{ff.name}", ff)
		ports = dict(
			CLK=get_sig(m, cfg, ff.clk, prefix=f"{lc}_"),
			D=get_sig(m, cfg, ff.data, prefix=f"{lc}_"),
			Q=cfg.ff.q
		)
		if cfg.ff.sr is not None:
			ports["SR"] = get_sig(m, cfg, ff.sr, prefix=f"{lc}_")
		if cfg.ff.en is not None:
			ports["EN"] = get_sig(m, cfg, ff.en, prefix=f"{lc}_")
		if cfg.has_init:
			ports["INIT"] = "CFG_MODE"
		m.add_submod(lut, f"{lc}_{ff.name}_i", **ports)
		ff.finalise(f)
	# outputs
	for out_name, sig in cfg.outputs:
		m.add_assign(f"{lc}_{out_name}", get_sig(m, cfg, sig, prefix=f"{lc}_"))
	print("", file=f)

def generate_clb(name: str, f, cfg: CLBConfig):
	inputs = ["CFG_MODE", ] + [ctrl.name for ctrl in cfg.glb_ctrl]
	outputs = []

	for i in range(cfg.num_lcs):
		lc = chr(ord('A') + index)
		inputs += [f"{lc}_I{i}" for i in range(cfg.lut_k)]
		inputs += [f"{lc}_{x}" for x in cfg.extra_inputs]
		outputs += [f"{lc}_{o}" for o, _ in cfg.outputs]
	m = ModuleGen(name, inputs=inputs, outputs=outputs)
	if len(m.lutram_lcs) > 0:
		m.gen_cfg_storage = True
	# Configurably invertible global inputs
	for ctrl in cfg.glb_ctrl:
		if ctrl.can_invert:
			inv = m.cfg(f"{ctrl.name}_INV")
			m.add_prim("clb_xor", a=ctrl.name, b=inv, x=f"{ctrl.name}_I")
	# LUTRAM global control set
	if len(m.lutram_lcs) > 0:
		wclk = get_sig(m, cfg, cfg.lutram_ctrl.wr_clock)
		we = get_sig(m, cfg, cfg.lutram_ctrl.wr_en)
		lutram_en = m.cfg("LUTRAM_EN")
		m.add_prim("clb_and", a=we, b=lutram_en, x="we_gate")
		m.add_prim("clb_andnot", a="we_gate", b="CFG_MODE", x="lutram_we")
		m.add_prim("clb_wstrb_gen", wclk=wclk, we=we, strobe="lutram_strobe")
		m.add_vector_sig('lutram_wr_strobe', 2*cfg.lut_k)
		wa = f"{{{', '.join(x for x in reversed(cfg.lutram_ctrl.wr_addr))}}}"
		m.add_prim("clb_wr_decode", addr=wa, strobe="lutram_strobe", dec="lutram_wr_strobe", param_K=str(cfg.lut_k))
	# the LCs themselves
	for i in range(cfg.num_lcs):
		_generate_lc(cfg, m, i)
	print("// Main CLB", file=f)
	m.finalise(f)
	return m

if __name__ == '__main__':
	# nice challenging config
	cfg = CLBConfig(
		num_lcs=8,
		lut_k=5,
		extra_lut_taps=[LUTTap("LUT_O4A", 4, 0), LUTTap("LUT_O4B", 4, 1)],
		extra_inputs=["X", ],
		lutram_lcs=dict(i: LUTRamConfig(wr_data="X") for i in range(6)), # first 6 LCs have LUTRAM
		lutram_ctrl=LUTRamControl(
			wr_clock="CLK",
			wr_en="WE",
			wr_addr=[f"H_I{i}" for i in range(5)],
		),
		flipflops=[
			FFConfig(name="FF0", data=CMux("FF0MUX", "LUT_O4A", "LUT_O", "X"), q="Q0",
				clk="CLK", sr="SR0", ce="CE0", gate_sr=True, gate_en=True,
				has_init=True, config_init=True, en_over_sr=False
			),
			FFConfig(name="FF1", data=CMux("FF1MUX", "LUT_O4B", "LUT_O"), q="Q1",
				clk="CLK", sr="SR1", ce="CE1", gate_sr=True, gate_en=True,
				has_init=True, config_init=True, en_over_sr=False
			),
		],
		outputs=[
			"O0", CMux("O0MUX", "FF0MUX", "Q0"),
			"O1", CMux("O1MUX", "FF1MUX", "Q1"),
		],
		glb_ctrl=[
			GlbControl("CLK", can_invert=True),
			GlbControl("CE0", can_invert=False), GlbControl("CE1", can_invert=False),
			GlbControl("SR0", can_invert=True), GlbControl("SR1", can_invert=True),
			GlbControl("WE", can_invert=True)
		],
	)
	with open(sys.argv[1], "w") as f:
		generate_clb("TEST_CLB", f, cfg)
