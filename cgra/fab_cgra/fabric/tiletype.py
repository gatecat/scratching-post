from amaranth import *
from amaranth.hdl.rec import Layout
from dataclasses import dataclass
from .bel import *
from .fabric import FabricConfig
from enum import Enum

class GridDir(Enum):
    N = 0
    E = 1
    S = 2
    W = 3
    J = 4 # JUMP
    def opposite(self):
        if self == N: return S
        if self == E: return W
        if self == S: return N
        if self == W: return E
        if self == J: return J

@dataclass
class TilePort:
    dir: GridDir
    src: str|None = None
    dx: int = 0
    dy: int = 0
    dst: str|None = None
    width: int = 1
    shape: int|Shape|Layout = 1 # for CGRA signals

# TODO: work out how to do nice strongly typed switch matrix
class Tile(Elaboratable):
    def __init__(self, name: str, fcfg: FabricConfig, ports: list[TilePort], bels: list[Bel], switch_matrix):
        self.name = name
        self.fcfg = FabricConfig
        self.route_ports = ports
        self.bels = bels
        self.switch_matrix = switch_matrix
        self.config_bits = []
        # create signals
        if len(fcfg.num_clocks) > 0:
            self.gclocki = Signal(fcfg.num_clocks)
            if not fcfg.ext_clktree:
                # ripple clocktree
                self.gclocko = Signal(fcfg.num_clocks)
        # setup config bits...
    def has_config(self):
        return len(self.config_bits) > 0

    def toplevel_ports(self): # (name, signal, edge)
        # hardcoded ports that we might have
        def_ports = [
            ("gclocki", GridDir.S),
            ("gclocko", GridDir.N),
            ("cfg_strbi", GridDir.S),
            ("cfg_strbo", GridDir.N),
            ("cfg_datai", GridDir.W),
            ("cfg_datao", GridDir.E),
        ]
        top_ports = [(n, getattr(self, n), d) for n, d in def_ports if hasattr(self, n)]
        for p in self.route_ports:
            if p.dir == GridDir.J:
                continue
            if p.src is not None:
                top_ports.append((p.src, getattr(self, p.src), p.dir)) # TODO: check directions
            if p.dst is not None:
                top_ports.append((p.dst, getattr(self, p.dst), p.dir.opposite())) # TODO: check directions
        return top_ports
