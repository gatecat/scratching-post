from dataclasses import dataclass
from ..tech.base import BaseTech

@dataclass
class FabricConfig:
    tech: BaseTech
    num_clocks: int = 1
    ext_clktree: bool = True
    row_bits_per_frame: int = 32
