from __future__ import annotations

from amaranth import *
from amaranth.hdl.rec import Layout
from dataclasses import dataclass
from typing import TypeAlias
from enum import Enum, IntEnum

from ..core.util import *

__all__ = ["Bel", "ConfigBit", "PortSpec", "PortDir"]

class PortDir(Enum):
    IN = 0
    OUT = 1

@dataclass
class PortSpec:
    name: str
    direction: PortDir
    shape: PortShape = 1
    external: bool = False
    shared: bool = False
    tile_wire: str|None = None # for manually wiring complex stuff

    def get_wire(self, bel: Bel):
        if self.tile_wire is not None:
            return self.tile_wire
        elif self.external:
            return self.name
        else:
            return f"{bel.prefix}_{self.name}"

class ConfigBit:
    name: str
    sig: Signal
    tags: list[tuple[str, int]]

class Configurable:
    # Type with helper functions for anything with configuration bits, keeping track of their meanings
    def __init__(self):
        self.cfg_bits: list[ConfigBit] = []
    def cfg_bit(self, name: str) -> Signal:
        sig = Signal(name=f"cfg_{name}")
        self.cfg_bits.append(ConfigBit(name=name, sig=sig, tags=[("", 1)]))
        return sig
    def cfg_enum(self, name: str, e: IntEnum) -> Signal:
        sig = Signal(shape=e, name=f"cfg_{name}")
        self.cfg_bits.append(ConfigBit(name=name, sig=sig, tags=[(k, v) for k, v in sorted(e, key=lambda x:x[1])]))
        return sig
    def cfg_word(self, name: str, w: int) -> Signal:
        sig = Signal(shape=w, name=f"cfg_{name}")
        self.cfg_bits.append(ConfigBit(name=name, sig=sig, tags=[(f"[{i}]", (1<<i)) for i in range(w)]))
        return sig
    def cfg_inst(self, sub_name: str, sub_inst):
        # Add a child of this, importing it's bit meanings into ours with a prefix
        for cfg in sub_inst.cfg_bits:
            self.cfg_bits.append(ConfigBit(name=f"{sub_name}.{cfg.name}", sig=cfg.sig, tags=cfg.tags))

    def cfg_count(self) -> int:
        return sum(len(cfg.sig) for cfg in self.cfg_bits)
    def cfg_bits(self):
        return Cat(*(cfg.sig for cfg in self.cfg_bits))

class Bel(Elaboratable, Configurable):
    def __init__(self, name, prefix):
        self.name = name
        self.prefix = prefix
    def get_ports(self) -> list[PortSpec]:
        assert False
