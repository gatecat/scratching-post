from amaranth import *
from amaranth.hdl.rec import Layout
from dataclasses import dataclass
from typing import TypeAlias
from enum import Enum, IntEnum

__all__ = ["Bel", "BelConfig", "PortSpec", "PortDir"]

class PortDir(Enum):
    IN = 0
    OUT = 1

@dataclass
class PortSpec:
    name: str
    direction: PortDir
    shape: int|Shape|Layout = 1
    external: bool = False
    shared: bool = False

class BelConfig:
    name: str
    sig: Signal
    tags: list[tuple[str, int]]

class Bel(Elaboratable):
    def __init__(self):
        self.cfg_bits: list[BelConfig] = []
    def get_ports(self) -> list[PortSpec]:
        assert False

    def cfg_bit(self, name: str) -> Signal:
        sig = Signal(name=f"cfg_{name}")
        self.cfg_bits.append(BelConfig(name=name, sig=sig, tags=[("", 1)]))
        return sig
    def cfg_enum(self, name: str, e: IntEnum) -> Signal:
        sig = Signal(shape=e, name=f"cfg_{name}")
        self.cfg_bits.append(BelConfig(name=name, sig=sig, tags=[(k, v) for k, v in sorted(e, key=lambda x:x[1])]))
        return sig
    def cfg_word(self, name: str, w: int) -> Signal:
        sig = Signal(shape=w, name=f"cfg_{name}")
        self.cfg_bits.append(BelConfig(name=name, sig=sig, tags=[(f"[{i}]", (1<<i)) for i in range(w)]))
        return sig
    def cfg_subbel(self, sub_name: str, sub_inst):
        for cfg in sub_inst.cfg_bits:
            self.cfg_bits.append(BelConfig(name=f"{sub_name}.{cfg.name}", sig=cfg.sig, tags=cfg.tags))

    def cfg_count(self) -> int:
        return sum(len(cfg.sig) for cfg in self.cfg_bits)
    def cfg_bits(self):
        return Cat(*(cfg.sig for cfg in self.cfg_bits))
