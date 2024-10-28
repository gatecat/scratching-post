from amaranth import *
from amaranth.lib import stream, wiring, data
from amaranth.lib.wiring import In, Out

class Depacketiser(wiring.Component):
    def __init__(self, header_layout):
        if header_layout.size % 8 != 0:
            raise ValueError(f"Header size must be exact number of bytes")

        self._header_layout = header_layout

        super().__init__({
            "bytes_in": In(stream.Signature(data.StructLayout({
                "data": 8,
                "end":  1,
            }))),
            "header_out": Out(stream.Signature(header_layout, always_ready=True)),
            "payload_out": Out(stream.Signature(data.StructLayout({
                "data": 8,
                "end":  1,
            }))),
            "error": Out(1),
        })
    def elaborate(self, platform):
        m = Module()
        header_len = self._header_layout.size
        header_bytes = header_len // 8
        header_sr = Signal(header_len)
        header_sr_next = Signal(header_len)
        byte_count = Signal(range(header_len + 2))

        m.d.comb += header_sr_next.eq(Cat(header_sr[8:], self.bytes_in.payload.data))

        m.d.sync += self.error.eq(0)

        # Header processing
        with m.If(self.bytes_in.valid):

            with m.If(byte_count < header_bytes):
                m.d.sync += [
                    self.header_out.valid.eq(0),
                    byte_count.eq(byte_count + 1),
                    header_sr.eq(header_sr_next),
                ]
            with m.If(byte_count == (header_bytes - 1)):
                m.d.sync += [
                    self.header_out.valid.eq(1),
                    self.header_out.payload.eq(header_sr_next)
                ]

            with m.If(self.bytes_in.ready & self.bytes_in.payload.end): # end of packet
                with m.If(byte_count < (header_bytes - 1)):
                    m.d.sync += self.error.eq(1) # incomplete header
                m.d.sync += byte_count.eq(0)

        # Stream processing
        with m.If(byte_count >= header_bytes):
            m.d.comb += [
                self.bytes_in.ready.eq(self.payload_out.ready),
                self.payload_out.valid.eq(self.bytes_in.valid)
            ]
        with m.Else():
            m.d.comb += self.bytes_in.ready.eq(1)

        m.d.comb += self.payload_out.payload.eq(self.bytes_in.payload)
        return m


class HeaderEndianSwapper(wiring.Component):
    def __init__(self, stream_type):
        super().__init__({
            "header_in": In(stream_type),
            "header_out": Out(stream_type),
        })
    def elaborate(self, platform):
        m = Module()

        for name, field in self.header_in.payload.shape():
            if field.width <= 8:
                m.d.comb += getattr(self.header_out.payload, name).eq(getattr(self.header_in.payload, name))
            else:
                if field.width % 8 != 0:
                    raise ValueError(f"multi-byte field {name} is not an exact number of bytes")
                if field.offset % 8 != 0:
                    raise ValueError(f"multi-byte field {name} is not byte-aligned")

                field_bytes = field.width // 8

                for byte in range(field_bytes):
                    m.d.comb += getattr(self.header_out.payload, name)[byte*8:(byte+1)*8].eq(
                        getattr(self.header_in.payload, name)[(field_bytes - byte - 1)*8:(field_bytes - byte)*8])

        m.d.comb += [
            self.header_out.valid.eq(self.header_in.valid),
#            self.header_in.ready.eq(self.header_out.ready)
        ]
        return m
