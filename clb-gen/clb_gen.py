from module_gen import *
from complex_ff import FFConfig, gen_dff
from lut_muxtree import LUTTap, gen_lut
from module_config import *

from dataclasses import dataclass, field

@dataclass
class FFControl:
	name: str
	can_invert: bool = False

@dataclass
class CLBConfig:
	num_lcs: int = 8
	lut_k: int = 4
	extra_lut_taps: list[LUTTap] = field(default_factory=list)
	extra_inputs: list[str] = field(default_factory=list)
	with_lutram: bool = False
	flipflops: list[FFConfig] = field(default_factory=list)
	# TODO: carry
	ff_ctrl: list[str] = field(default_factory=list)
	outputs: list[str] = field(default_factory=list)

def generate_clb (
	cfg: CLBConfig
	):
	pass

	
