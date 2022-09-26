from dataclasses import dataclass

@dataclass
class FabricConfig:
    num_clocks: int = 1
    ext_clktree: bool = True
    row_bits_per_frame: int = 32
