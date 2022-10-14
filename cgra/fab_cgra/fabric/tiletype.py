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
        if self == GridDir.N: return GridDir.S
        if self == GridDir.E: return GridDir.W
        if self == GridDir.S: return GridDir.N
        if self == GridDir.W: return GridDir.E
        if self == GridDir.J: return GridDir.J

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
        self.bpf = fcfg.row_bits_per_frame
        self.frame_count = (self.total_size + (self.bpf - 1)) // self.bpf
        self.frame_strobe = Signal(self.frame_count)
        self.frame_data = Signal(fcfg.row_bits_per_frame)
        self.config_bits = Signal(total_size)
        # TODO: non-default bit layout

    def elaborate(self, platform):
        m = Module()
        t = self.fcfg.tech
        for (i, bit) in enumerate(self.config_bits):
            t.add_latch(m=m,
                d=self.frame_data[i % self.bpf], e=self.frame_strobe[i // self.bpf], q=self.config_bits[i],
                name=f"cfg{i}"
            )
        return m

def _expand_matrix_entry(switch_matrix):
    # expand a classic FABulous style switch matrix entry
    # foo_[a|b][0|1] -> (foo_a0, foo_a1, foo_b0, foo_b1)
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

def _parse_fab_switch_matrix(entry):
    # if it's a classic FABulous style string, expand it
    dst_str, _, src_str = entry.partition(",")
    dsts = _expand_matrix_entry(dst_str)
    srcs = _expand_matrix_entry(src_str)
    return (dsts, srcs)

class SwitchMatrix:
    def __init__(self):
        self.matrix = {}
    def add(self, entry, srcs=None):
        # add an entry to the switch matrix, either classic FABulous style as a single string or str being the dst and rhs being the list of sources
        if srcs is not None:
            for src in srcs:
                self.add_pip(entry, src)
        else:
            assert not isinstance(srcs, str), srcs
            for dst, src in zip(*_parse_fab_switch_matrix(entry)):
                self.add_pip(dst, src)
    def add_pip(self, dst, src):
        if dst not in self.matrix:
            self.matrix[dst] = []
        if src not in self.matrix[dst]:
            self.matrix[dst].append(src)
    def items(self):
        return self.matrix.items()

class _TileSwitchMatrix(Elaboratable):
    def __init__(self, t: Tile):
        self.t = t
        self.cfg = Configurable()
        # Prepare the config bit layout
        self.dst2bits = {}
        for dst, srcs in self.t.switch_matrix.items():
            # use split_mux to get the bit pattern enum
            if len(srcs) == 1:
                continue
            self.dst2bits[dst] = self.cfg.enum(dst,
                self.t.tech.split_mux(m=None, inputs=[(None, src) for src in srcs], sel=None, y=None, dry_run=True, name=f"cfg_{dst}"))
    def elaborate(self, platform):
        m = Module()
        for dst, srcs in self.t.switch_matrix.items():
            if len(srcs) == 1:
                m.d.comb += self.t.wires[dst].eq(self.t.wires[srcs[0]])
            else:
                sel = self.dst2bits[dst]
                self.t.tech.split_mux(m=m,
                    inputs=[(self.t.wires[src], src) for src in srcs], sel=sel, y=self.t.wires[dst],
                    dry_run=False, name=f"cfg_{dst}")
        return m

# TODO: work out how to do nice strongly typed switch matrix
class Tile(Elaboratable):
    def __init__(self, name: str, fcfg: FabricConfig, ports: list[TilePort], bels: list[Bel], switch_matrix: SwitchMatrix):
        self.name = name
        self.fcfg = fcfg
        self.tech = fcfg.tech
        self.route_ports = ports
        self.bels = bels
        self.switch_matrix = switch_matrix
        self.config_bits = []
        self.cfg = Configurable()
        self.wires = {}
        # create signals
        if fcfg.num_clocks > 0:
            self.gclocki = Signal(fcfg.num_clocks)
            if not fcfg.ext_clktree:
                # ripple clocktree
                self.gclocko = Signal(fcfg.num_clocks)
        # top port signals
        for port in self.route_ports:
            for wire in (port.src, port.dst):
                if wire is not None and not hasattr(self, wire):
                    wire_len = max(1, abs(port.dx) + abs(port.dy))
                    channel_width = port.width * wire_len
                    sig = Signal(name=wire, shape=port_width(port.shape)*channel_width)
                    setattr(self, wire, sig)
                    # sub-wires
                    for i in range(port.width):
                        ofs = (wire_len - 1) * port.width if (wire == port.src) else 0
                        self.wires[f"{wire}{i}"] = sig[(ofs+i)*port_width(port.shape) : (ofs+i+1)*port_width(port.shape)]
        # setup config bits...
        #  - bel config
        for bel in bels:
            self.cfg.inst(f"{bel.name}.", bel.cfg)
            for port in bel.get_ports():
                tile_wire = port.get_wire(bel)
                if tile_wire not in self.wires:
                    self.wires[tile_wire] = Signal(shape=port.shape, name=tile_wire)
        # prepare submodules
        self.sb_i = _TileSwitchMatrix(self)
        self.cfg.inst("", self.sb_i.cfg)
        if self.cfg.count() > 0:
            self.cfgmem_i = _TileConfig(self.fcfg, self.cfg.count())
            self.cfg_datai = Signal(fcfg.row_bits_per_frame)
            self.cfg_strbi = Signal(len(self.cfgmem_i.frame_strobe))
            self.cfg_datao = Signal(fcfg.row_bits_per_frame)
            self.cfg_strbo = Signal(len(self.cfgmem_i.frame_strobe))
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
    def elaborate(self, platform):
        m = Module()
        if self.fcfg.num_clocks > 0:
            m.d.comb += ClockSignal().eq(self.gclocki[0])
        # add submodule instances
        for b in self.bels:
            setattr(m.submodules, f"bel_{b.name}", b)
            # connect bel ports to tile wires
            for port in b.get_ports():
                # TODO: record ports
                if port.dir == PortDir.OUT:
                    m.d.comb += self.wires[port.get_wire(b)].eq(getattr(b, port.name))
                else:
                    m.d.comb += getattr(b, port.name).eq(self.wires[port.get_wire(b)])
            if hasattr(b, "gclocki"):
                m.d.comb += getattr(b, "gclocki").eq(self.gclocki)
        m.submodules.sb_i = self.sb_i
        if self.cfg.count() > 0:
            # add config memory and connect up
            m.submodules.cfgmem_i = self.cfgmem_i
            m.d.comb += [
                self.cfgmem_i.frame_data.eq(self.cfg_datai),
                self.cfgmem_i.frame_strobe.eq(self.cfg_strbi),
                self.cfg.sigs().eq(self.cfgmem_i.config_bits),
            ]
        return m

