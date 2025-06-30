from amaranth import *
from amaranth.lib import enum, data, stream, wiring
from amaranth.lib.wiring import In, Out

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

        super().__init__({
            "aw": Out(self.aw_signature()),
            "w": Out(self.w_signature()),
            "b": In(self.b_signature()),
            "ar": Out(self.ar_signature()),
            "r": In(self.r_signature()),
        })

if __name__ == '__main__':
    Signature(addr_width=32, data_width=32)
