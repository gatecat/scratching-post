from ..fabric.tiletype import *
from ..fabric.bel import *
from ..fabric.fabric import *
from itertools import product

from .cgra_elem import CgraElem

base_width = 12
sig_width = base_width + 1

ports = [
    TilePort(dir=GridDir.N, src="CLRBEG", dy=-1, dst="CLREND", width=1, shape=1), # global
    TilePort(dir=GridDir.N, src="N1BEG", dy=-1, dst="N1END", width=2, shape=sig_width),
    TilePort(dir=GridDir.S, src="S1BEG", dy=1, dst="S1END", width=2, shape=sig_width),
    TilePort(dir=GridDir.E, src="E1BEG", dx=1, dst="E1END", width=2, shape=sig_width),
    TilePort(dir=GridDir.W, src="W1BEG", dx=-1, dst="W1END", width=2, shape=sig_width),
]

def gen_switch_matrix():
	result = SwitchMatrix()
	for dst_d, dst_i in product("NESW", (0, 1)):
		dst = f"{dst_d}1BEG{dst_i}"
		for src_d, src_i in product("NESW", (0, 1)):
			if src_d == dst_d and src_i != dst_i:
				# TODO is this the best one to replace
				result.add(dst, ["A_Q", ]) # elem output
			else:
				result.add(dst, [f"{src_d}1END{src_i}", ]) # routing
	for dst in ("A_A", "A_B"):
		for src_d, src_i in product("NESW", (0, 1)):
			result.add(dst, [f"{src_d}1END{src_i}", ]) # routing
	result.add("A_CLR", ["CLREND0", ])
	result.add("CLRBEG0", ["CLREND0", ]) # route through CLR
	return result

if __name__ == '__main__':
    import sys
    from amaranth.back import verilog
    from .switch_matrix import *
    from ..tech.base import BaseTech

    tech = BaseTech()
    cfg = FabricConfig(tech)
    class CgraTile(Tile):
        def __init__(self, cfg):
            bels = [
                CgraElem(name="A", prefix="A_", tech=tech, base_width=base_width),
            ]
            super().__init__(name="LogicTile", fcfg=cfg, ports=ports, bels=bels, switch_matrix=gen_switch_matrix())

        def elaborate(self, platform):
            m = super().elaborate(platform)
            m.d.comb += ResetSignal().eq(0)
            return m
    tile = CgraTile(cfg)
    tile_ports = [x[1] for x in tile.toplevel_ports()]
    with open(sys.argv[1], "w") as f:
        f.write(verilog.convert(tile, name="cgra_mul_tile", ports=tile_ports))
    with open(f"{sys.argv[1]}.features", "w") as f:
       tile.cfg.write_bitmap(f)
