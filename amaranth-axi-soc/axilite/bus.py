from amaranth import *
from amaranth.lib import enum, data, stream, wiring
from amaranth.lib.wiring import In, Out

from amaranth_soc.memory import MemoryMap

class Protection(data.Struct):
    privileged:  1
    non_secure:  1
    instruction: 1

class Response(enum.Enum, shape=2):
    OKAY   = 0
    EXOKAY = 1
    SLVERR = 2
    DECERR = 3


class Signature(wiring.Signature):
    def aw_signature(self):
        return stream.Signature(data.StructLayout({
            "addr": self._addr_width,
            "prot": Protection,
        }))

    def w_signature(self):
        return stream.Signature(data.StructLayout({
            "data": self._data_width,
            "strb": self._data_width // 8,
        }))

    def b_signature(self):
        return stream.Signature(data.StructLayout({
            "resp": Response
        }))

    def ar_signature(self):
        return stream.Signature(data.StructLayout({
            "addr": self._addr_width,
            "prot": Protection,
        }))

    def r_signature(self):
        return stream.Signature(data.StructLayout({
            "data": self._data_width,
            "resp": Response,
        }))


    def __init__(self, *, addr_width, data_width):
        if not isinstance(addr_width, int) or addr_width < 0:
            raise TypeError(f"Address width must be a non-negative integer, not {addr_width!r}")
        if data_width not in (32, 64):
            raise ValueError(f"Data width must be one of 32 or 64, not {data_width!r}")

        self._addr_width  = addr_width
        self._data_width  = data_width
        self._memory_map = None

        super().__init__({
            "aw": Out(self.aw_signature()),
            "w": Out(self.w_signature()),
            "b": In(self.b_signature()),
            "ar": Out(self.ar_signature()),
            "r": In(self.r_signature()),
        })

    @property
    def memory_map(self):
        if self._memory_map is None:
            raise AttributeError(f"{self!r} does not have a memory map")
        return self._memory_map

    @memory_map.setter
    def memory_map(self, memory_map):
        if not isinstance(memory_map, MemoryMap):
            raise TypeError(f"Memory map must be an instance of MemoryMap, not {memory_map!r}")
        if memory_map.data_width != 8:
            raise ValueError(f"Memory map has data width {memory_map.data_width}, which is "
                             f"not the same as bus interface granularity 8")
        if memory_map.addr_width != self._addr_width:
           raise ValueError(f"Memory map has address width {memory_map.addr_width}, which is "
                             f"not the same as the bus interface effective address width "
                             f"{self._addr_width}")
        self._memory_map = memory_map


if __name__ == '__main__':
    Signature(addr_width=32, data_width=32)
