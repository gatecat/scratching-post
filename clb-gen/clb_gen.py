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
class CLBConfig:
	num_lcs: int = 8
	lut_k: int = 4
	extra_lut_taps: list[LUTTap] = field(default_factory=list)
	extra_inputs: list[str] = field(default_factory=list)
	lutram_lcs: dict[int, LUTRamConfig] = field(default_factory=dict)
	flipflops: list[FFConfig] = field(default_factory=list)
	# TODO: carry
	glb_ctrl: list[GlbControl] = field(default_factory=list)
	outputs: list[str] = field(default_factory=list)

def _generate_lc(cfg: CLBConfig, m: ModuleGen, f, index):
	lc = chr(ord('A') + index)
	print(f"// Submodules for LC {lc}", file=f)
	lut_inputs = [f"{lc}_I{i}" for i in range(cfg.lut_k)]
	extra_inputs = [f"{lc}_{x}" for x in cfg.extra_inputs]

	# generate LUT (TODO not a LUT or complex LUT)
	lut = gen_lut(f"{lc}_LUT", k, cfg.extra_lut_taps, with_lutram=index in cfg.lutram_lcs)
	ports = dict(
		I=f"{{{', '.join(reversed(lut_inputs))}}}",
		O=f"{lc}_O",
	)
	for tap in extra_lut_taps:
		ports[tap.name] = f"{lc}_{tap.name}"
	if index in cfg.lutram_lcs:
		ports["CFG_MODE"] = "CFG_MODE"
		ports["WR_STROBE"] = "RAM_WR_STROBE"
		ports["WR_DATA"] = cfg.lutram_lcs[index].wr_data
	m.add_submod(lut, f"{lc}_LUT_i", **ports)
	lut.finalise(f)
	# TODO: carry
	# TODO: configuring bit/frame aspect ratio 
	# generate FFs
	for ff in cfg.flipflops:
		ff = gen_dff(f"{lc}_{ff.name}", ff)
		ports = dict(
			CLK=get_sig(m, cfg, ff.clk),
			D=get_sig(m, cfg, ff.data),
			Q=cfg.ff.q
		)
		if cfg.ff.sr is not None:
			ports["SR"] = get_sig(m, cfg, ff.sr)
		if cfg.ff.en is not None:
			ports["EN"] = get_sig(m, cfg, ff.en)
		if cfg.has_init:
			ports["INIT"] = "CFG_MODE"
		m.add_submod(lut, f"{lc}_{ff.name}_i", **ports)
		ff.finalise(f)
	print("", file=f)

def generate_clb(cfg: CLBConfig):
	pass

	
