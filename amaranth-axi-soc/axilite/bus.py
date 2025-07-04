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

    @property
    def addr_width(self):
        return self._addr_width

    @property
    def data_width(self):
        return self._data_width

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


    def create(self, *, path=None, src_loc_at=0):
        return Interface(addr_width=self.addr_width, data_width=self.data_width,
                         path=path, src_loc_at=1 + src_loc_at)

class Interface(wiring.PureInterface):
    def __init__(self, *, addr_width, data_width,
                 path=None, src_loc_at=0):
        super().__init__(Signature(addr_width=addr_width, data_width=data_width),
                         path=path, src_loc_at=1 + src_loc_at)
        self._memory_map = None

    @property
    def addr_width(self):
        return self.signature.addr_width

    @property
    def data_width(self):
        return self.signature.data_width

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
        if memory_map.addr_width != self.addr_width:
           raise ValueError(f"Memory map has address width {memory_map.addr_width}, which is "
                             f"not the same as the bus interface effective address width "
                             f"{self.addr_width}")
        self._memory_map = memory_map

    def __repr__(self):
        return f"wishbone.Interface({self.signature!r})"

# Decoder and arbiter logic based on LiteX: https://github.com/enjoy-digital/litex/blob/master/litex/soc/interconnect/axi/axi_lite.py

class _RequestCounter(wiring.Component):
    def __init__(self, max_requests=256):
        self._max_requests = max_requests
        super().__init__({
            "request":  In(1),
            "response": In(1),
            "stall": Out(1),
            "ready": Out(1),
        })
    def elaborate(self, platform):
        m = Module()
        counter = Signal(range(self._max_requests))
        full = Signal()
        empty = Signal()

        m.d.comb += [
            full.eq(counter == self._max_requests - 1),
            empty.eq(counter == 0),
            self.stall.eq(self.request & full),
            self.ready.eq(empty)
        ]

        with m.If(self.request & self.response):
            pass # net no change
        with m.Elif(self.request & ~full):
            m.d.sync += counter.eq(counter + 1)
        with m.Elif(self.response & ~empty):
            m.d.sync += counter.eq(counter - 1)

class _ArbiterImpl(Elaboratable):
    def __init__(self, bus, subs, addr, req, resp):
        self.bus = bus
        self.subs = subs
        self.addr = addr
        self.req = req
        self.resp = resp

    def elaborate(self, m):
        # Locking logic

        bus_a = getattr(self.bus, self.addr)
        bus_req = getattr(self.bus, self.req) if self.req is not None else None
        bus_resp = getattr(self.bus, self.resp)

        m = Module()
        m.submodules.lock = lock = _RequestCounter()
        m.d.comb = [
            lock.request.eq(bus_a.valid & bus_a.ready),
            lock.response.eq(bus_resp.valid & bus_resp.ready),
        ]

        sub_sel_dec = Signal(len(self.subs))
        sub_sel_reg = Signal(len(self.subs))
        sub_sel     = Signal(len(self.subs))

        # We need to hold the subordinate selected until all responses come back.
        m.d.comb += sub_sel_dec.eq(0)

        # Decoding logic
        with m.Switch(bus_a.payload.addr):
            for index, (sub_map, sub_name, (sub_pat, sub_ratio)) in enumerate(self.bus.memory_map.window_patterns()):
                with m.Case(sub_pat):
                    m.d.comb += sub_sel_dec[index].eq(1)

        with m.If(lock.ready):
            m.d.sync += sub_sel_reg.eq(sub_sel_dec)
            m.d.comb += sub_sel.eq(sub_sel_dec)
        with m.Else():
            m.d.comb += sub_sel.eq(sub_sel_reg)

        # Connect up subordinate buses

        for index, (sub_map, sub_name, (sub_pat, sub_ratio)) in enumerate(self.bus.memory_map.window_patterns()):
            sub_bus = self._subs[sub_map]

            sub_a = getattr(self.sub, self.addr)
            sub_req = getattr(self.sub, self.req) if self.req is not None else None
            sub_resp = getattr(self.sub, self.resp)

            # Address
            m.d.comb += [
                sub_a.payload.addr.eq(bus_a.payload.addr),
                sub_a.payload.prot.eq(bus_a.payload.prot),
                sub_a.valid.eq(bus_a.valid & sub_sel[index]),
            ]

            # Request (if applicable)
            if bus_req is not None:
                m.d.comb += [
                    sub_req.payload.eq(bus_req.payload),
                    sub_req.valid.eq(bus_req.valid & sub_sel[index]),
                ]

            # Response
            m.d.comb += sub_resp.ready.eq(bus_resp.ready & sub_sel[index])

            with m.If(sub_sel[index]):
                m.d.comb += bus_a.ready.eq(sub_a.ready & ~lock.stall)
                if bus_req is not None:
                    m.d.comb += bus_req.ready.eq(sub_req.ready & ~lock.stall)
                m.d.comb += [
                    bus_resp.payload.eq(sub_resp.payload),
                    bus_resp.valid.eq(sub_resp.valid),
                ]
        # TODO: DECERR generation
