from __future__ import annotations

from amaranth import *
from amaranth.hdl.rec import Layout
from dataclasses import dataclass
from .bel import *
from .fabric import FabricConfig
from ..core.util import *

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
    shape: int|Layout = 1 # for CGRA signals

class _TileConfig(Elaboratable):
    def __init__(self, fcfg: FabricConfig, total_size: int):
        self.fcfg = fcfg
        self.total_size = total_size
        self.frame_count = (self.total_size + (fcfg.row_bits_per_frame - 1)) // fcfg.row_bits_per_frame
        self.frame_strobe = Signal(self.frame_count)
        self.frame_data = Signal(fcfg.row_bits_per_frame)
        self.config_bits = Signal(total_size)
        # TODO: non-default bit layout

    def elaborate(self, platform):
        m = Module()
        return m

def _expand_matrix_entry(switch_matrix):
    result = []
    did_something = False
    while did_something:
        did_something = False
        expanded_result = []
        for r in result:
            if (bp := r.find('[')) != -1:
                ep = r.find(']')
                assert ep != -1, r
                pre = r[:bp]
                post = r[ep+1:]
                opts = r[bp+1:ep].split('|')
                for o in opts:
                    expanded_result.append(f"{pre}{o}{post}")
                did_something = True
            else:
                expanded_result.append(r)
        result = expanded_result
    return result

def _parse_switch_matrix(switch_matrix):
    result = {}
    for entry in switch_matrix:
        if isinstance(entry, tuple):
            assert isinstance(entry[0], str), entry
            assert isinstance(entry[1], list), entry
            for src in entry[1]:
                if entry[0] not in result: result[entry[0]] = []
                result[entry[0]].append(src)
        else:
            assert isinstance(entry, str), entry
            # if it's a classic FABulous style string, expand it
            dst_str, _, src_str = entry.partition(",")
            dsts = _expand_matrix_entry(dst_str)
            srcs = _expand_matrix_entry(src_str)
            for dst, src in zip(dsts, srcs):
                if dst not in result: result[dst] = []
                result[dst].append(src)
    return result

class _TileSwitchMatrix(Elaboratable, Configurable):
    def __init__(self, t: Tile):
        self.t = t
        self.route_graph = _parse_switch_matrix(t.switch_matrix)

# TODO: work out how to do nice strongly typed switch matrix
class Tile(Elaboratable, Configurable):
    def __init__(self, name: str, fcfg: FabricConfig, ports: list[TilePort], bels: list[Bel], switch_matrix):
        self.name = name
        self.fcfg = fcfg
        self.route_ports = ports
        self.bels = bels
        self.switch_matrix_desc = switch_matrix
        self.config_bits = []
        self.wires = {}
        # create signals
        if len(fcfg.num_clocks) > 0:
            self.gclocki = Signal(fcfg.num_clocks)
            if not fcfg.ext_clktree:
                # ripple clocktree
                self.gclocko = Signal(fcfg.num_clocks)
        # top port signals
        for port in self.route_ports:
            for wire in (p.src, p.dst):
                if wire is not None and not hasattr(self, wire):
                    setattr(self, wire, Signal(shape=layout_width(port.shape)*))
        # setup config bits...
        #  - bel config
        for bel in bels:
            self.cfg_inst(bel.name, bel)
            for port in bel.get_ports():
                tile_wire = port.get_wire(bel)
                if tile_wire not in self.wires:
                    self.wires[tile_wire] = Signal(shape=port.shape, name=tile_wire)
        # - TODO: routing....
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
        seen_ports = set()
        for p in self.route_ports:
            if p.dir == GridDir.J:
                continue
            if p.src is not None and p.src not in seen_ports:
                top_ports.append((p.src, getattr(self, p.src), p.dir)) # TODO: check directions
                seen_ports.add(p.src)
            if p.dst is not None and p.dst not in seen_ports:
                top_ports.append((p.dst, getattr(self, p.dst), p.dir.opposite())) # TODO: check directions
                seen_ports.add(p.dst)
        return top_ports
