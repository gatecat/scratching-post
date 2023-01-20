from amaranth import *
from amaranth.sim import Simulator, Delay, Settle
from amaranth_soc import wishbone

"""
Combined QSPI Flash and PSRAM controller for the demo SoC

This allows both XIP storage and main memory to be connected with a minimum number of external pins. 

It provides 4 8-bit control registers as well as a Wishbone bus interface.
The upper bit of the Wishbone bus selects flash (0) or RAM (1). Lower bits select chips and then
addresses within those chips.

The control registers are:

sys_cfg:
  bit 0: bitbang enable (wishbone access blocked; use bitbang registers for manual IO)
  bit 1: QSPI enable
  bit 2: RAM device size (0=64M, 1=128M)
  default: 0b00000000

pad_count:
  bits 3..0: padding bits for flash
  bits 7..4: padding bits for RAM
  default: 0x88

max_burst:
  bits 7..0: max burst length in words
  default: 0x10

  must be set so as to not violate the PSRAM maximum CS high time

bitbang:
  bit 0: read DI
  bit 1: write DO
  bit 2: write CLK
  bit 7..3: write CS

**IMPORTANT**: as some configuration will be required to take flash out of slow SPI mode, and bitbang
accesses cannot be done whilst running code in XIP mode; they system must have some other available
internal SRAM to copy the flash setup code into and run it out of.

For a further pin reduction, an "encoded" chip select mode is supported. An external active low decoder
such as the 74xx138 will be required.
"""
class QspiMem(Elaboratable):
    def __init__(self, *,
        max_devs=7, encoded_cs=True):
        self.max_devs = max_devs
        self.abits = 24
        self.encoded_cs = encoded_cs
        # total size of the address space
        self.total_space = 1 + max_devs.bit_length() + self.abits
        self.data_bus = wishbone.Interface(addr_width=self.total_space-2, # -2 because WB has word addresses
                                      data_width=32, granularity=8)
        # the IO
        self.d_i = Signal(4)
        self.d_o = Signal(4)
        self.d_oe = Signal(4)
        self.clk_o = Signal()
        self.clk_oe = Signal()
        self.cs_width = self.max_devs.bit_length() if self.encoded_cs else self.max_devs
        self.cs_o = Signal(self.cs_width)
        self.cs_oe = Signal(self.cs_width)
        self.io = [self.d_i, self.d_o, self.d_oe,
            self.clk_o, self.clk_oe, self.cs_o, self.cs_oe]
        # config registers
        self.sys_cfg = Signal(8)
        self.pad_count = Signal(8)
        self.max_burst = Signal(8)
        self.bitbang_i = Signal(8)
        self.bitbang_o = Signal()
        self.config = [self.sys_cfg, self.pad_count, self.max_burst, self.bitbang_i]
    def elaborate(self, platform):
        m = Module()
        latched_adr = Signal(len(self.data_bus.adr))
        latched_we = Signal()
        counter = Signal(8)
        next_counter = Signal(8)
        wait_count = Signal(4)
        burst_count = Signal(8)
        sr = Signal(32)
        sr_shift = Signal(8)
        clk = Signal()
        dq_out = Signal(4)
        dq_oe = Signal(4)
        quad = Signal()
        shift_in = Signal()
        csn = Signal(self.cs_width)

        cfg_bb, cfg_quad, cfg_ram128 = self.sys_cfg[:3]

        # partial write handling
        xfer_ofs = Signal(2)
        xfer_cnt = Signal(3)

        # counter and clock generation
        with m.If(csn.all()):
            # Reset clock if nothing active
            m.d.sync += clk.eq(0)
        with m.Elif(counter.any()):
            m.d.sync += clk.eq(~clk)
            m.d.comb += next_counter.eq(counter)
            with m.If(clk):
                m.d.comb += next_counter.eq(counter-Mux(quad, 4, 1))
            m.d.sync += counter.eq(next_counter)
        # IO shift register
        with m.If(counter.any()):
            # move output shift register (sample/output data) before negedge
            # move input shift register (sample/output data) before posedge
            with m.If(Mux(shift_in, ~clk, clk)):
                with m.If(quad):
                    m.d.sync += sr.eq(Cat(self.d_i, sr[:-4]))
                with m.Else():
                    m.d.sync += sr.eq(Cat(self.d_i[1], sr[:-1]))
        with m.If(quad):
            m.d.comb += dq_out.eq(sr[-4:])
            m.d.comb += dq_oe.eq(Repl(~shift_in, 4))
        with m.Else():
            m.d.comb += dq_out.eq(Cat(sr[-1], C(0, 3)))
            m.d.comb += dq_oe.eq(0b0001)
        # main command FSM
        with m.FSM() as fsm:
            with m.State("IDLE"):
                m.d.sync += [
                    counter.eq(0),
                    quad.eq(0),
                    csn.eq(-1),
                    shift_in.eq(0),
                    wait_count.eq(0),
                    burst_count.eq(0),
                    self.data_bus.ack.eq(0),
                ]
                with m.If(self.data_bus.stb & self.data_bus.cyc):
                    # Wishbone transaction has occurred
                    m.d.sync += [
                        latched_adr.eq(self.data_bus.adr),
                        latched_we.eq(self.data_bus.we),
                    ]
                    # Partial write handling
                    with m.If(self.data_bus.we):
                        with m.Switch(self.data_bus.sel):
                            with m.Case(0b1111): m.d.sync += [xfer_ofs.eq(0b00), xfer_cnt.eq(4)]
                            with m.Case(0b1100): m.d.sync += [xfer_ofs.eq(0b10), xfer_cnt.eq(2)]
                            with m.Case(0b0011): m.d.sync += [xfer_ofs.eq(0b00), xfer_cnt.eq(2)]
                            with m.Case(0b1000): m.d.sync += [xfer_ofs.eq(0b11), xfer_cnt.eq(1)]
                            with m.Case(0b0100): m.d.sync += [xfer_ofs.eq(0b10), xfer_cnt.eq(1)]
                            with m.Case(0b0010): m.d.sync += [xfer_ofs.eq(0b01), xfer_cnt.eq(1)]
                            with m.Case(0b0001): m.d.sync += [xfer_ofs.eq(0b00), xfer_cnt.eq(1)]
                            with m.Default():
                                # ** ERROR: unsupported
                                pass
                    with m.Else():
                        m.d.sync += [xfer_ofs.eq(0b00), xfer_cnt.eq(4)]
                    # Select device
                    dev = Signal(range(self.max_devs))
                    # flash always 24-bit per chip, RAM 24 or 23 selectable
                    with m.If(~self.data_bus.adr[-1] | cfg_ram128):
                        m.d.comb += dev.eq(self.data_bus.adr[-(self.max_devs.bit_length()+1):-1])
                    with m.Else():
                        m.d.comb += dev.eq(self.data_bus.adr[-(self.max_devs.bit_length()+2):-2])
                    # two CSN styles, with or without external decoder
                    if self.encoded_cs:
                        m.d.sync += csn.eq(dev)
                    else:
                        m.d.sync += csn.eq(~(0b1 << dev))
                    m.next = "SEND_CMD"
            with m.State("SEND_CMD"):
                with m.If(latched_we & cfg_quad): cmd = 0x38 # quad write
                with m.Elif(latched_we & cfg_quad): cmd = 0x02 # SPI write
                with m.Elif(~latched_we & cfg_quad):  cmd = 0xEB # quad fast read
                with m.Else(): cmd = 0x0B # SPI fast read
                m.d.sync += [
                    counter.eq(8),
                    sr[-8:].eq(cmd),
                ]
                m.next = "WAIT_CMD"
            with m.State("WAIT_CMD"):
                with m.If(next_counter == 0): # command done
                    m.d.sync += [
                        sr[8:].eq(Cat(
                            xfer_ofs,
                            Mux(~self.data_bus.adr[-1] | cfg_ram128, self.data_bus.adr[:22], self.data_bus.adr[:21]))
                        ),
                        sr[:8].eq(0xFF), # disable CRM
                        counter.eq(Mux(~self.data_bus.adr[-1] & cfg_quad & ~latched_we, 32, 24)), # flash quad reads require mode bits
                        quad.eq(cfg_quad),
                    ],
                    m.next = "WAIT_ADDR"
            with m.State("WAIT_ADDR"):
                with m.If(next_counter == 0):
                    with m.If(latched_we):
                        # write data
                        # gotta do some shuffling to deal with
                        #  - upper byte of SR is shifted first; little endian so this should be LSB of data bus
                        #  - for partial writes; need to have the actually-being-written part in the upper byte of SR
                        m.d.sync += [
                            sr[24:32].eq(self.data_bus.word_select(xfer_ofs, 8)),
                            sr[16:24].eq(self.data_bus.word_select(xfer_ofs+1, 8)),
                            sr[ 8:16].eq(self.data_bus[16:24]),
                            sr[ 0: 8].eq(self.data_bus[24:32]),
                            counter.eq(8 * xfer_cnt),
                        ]
                        m.next = "WAIT_WRITE"
                    with m.Else():
                        # pad bits
                        m.d.sync += [
                            counter.eq(Mux(self.data_bus.adr[-1], self.pad_count[4:], self.pad_count[:4])),
                        ]
                        m.next = "WAIT_DUMMY"
            with m.State("WAIT_WRITE"):
                with m.If(next_counter == 0):
                    m.d.sync += [self.data_bus.ack.eq(1), wait_count.eq(9), burst_count.eq(burst_count+1)]
                    with m.If(xfer_cnt == 4):
                        # currently, only full transactions can have a continuation
                        m.next = "WAIT_NEXT"
                    with m.Else():
                        m.next = "IDLE"
            with m.State("WAIT_DUMMY"):
                with m.If(next_counter == 1):
                    # switch output to input
                    m.d.sync += [shift_in.eq(1)]
                with m.If(next_counter == 0):
                    m.d.sync += [counter.eq(32)]
                    m.next = "WAIT_READ"
            with m.State("WAIT_READ"):
                with m.If(next_counter == 0):
                    m.d.sync += [self.data_bus.ack.eq(1), wait_count.eq(9), burst_count.eq(burst_count+1)]
                    m.next = "WAIT_NEXT"
            with m.State("WAIT_NEXT"):
                m.d.sync += [self.data_bus.ack.eq(0), wait_count.eq(wait_count-1)]
                with m.If(wait_count == 0):
                    # timeout waiting for continuation
                    m.next = "IDLE"
                with m.If(latched_adr[-1] & burst_count == self.max_burst):
                    # RAM has a maximum CS low time and burst length that must be obeyed
                    m.next = "IDLE"
                with m.If(self.data_bus.stb & self.data_bus.cyc & ~self.data_bus.ack):
                    # new transaction received
                    # check if it's a valid continuation
                    with m.If(
                            (self.data_bus.we == latched_we) & # same dir
                            (self.data_bus.adr[8:] == latched_adr[8:]) & # same page
                            (self.data_bus.adr[:8] == (latched_adr[:8]+1)) & # one higher
                            (~self.data_bus.we | self.data_bus.sel.all()) # not partial
                        ):
                        m.d.sync += [
                            counter.eq(4),
                            latched_adr.eq(self.data_bus.adr),
                        ]
                        with m.If(latched_we):
                            m.next = "WAIT_WRITE"
                        with m.Else():
                            m.next = "WAIT_READ"
                    with m.Else():
                        m.next = "IDLE"

        m.d.comb += [
            self.data_bus.dat_r.eq(sr),
        ]
        # bitbang mode handling
        with m.If(cfg_bb):
            m.d.comb += [
                self.d_o.eq(Cat(self.bitbang_i[0], C(0, 3))),
                self.d_oe.eq(0b0001 & Repl(~ResetSignal(), 4)),
                self.clk_o.eq(self.bitbang_i[2]),
                self.cs_o.eq(self.bitbang_i[3:]),
            ]
        with m.Else():
            m.d.comb += [
                self.d_o.eq(dq_out),
                self.d_oe.eq(dq_oe & Repl(~ResetSignal(), 4)),
                self.clk_o.eq(clk),
                self.cs_o.eq(csn),
            ]
        m.d.comb += [
            self.clk_oe.eq(~ResetSignal()),
            self.cs_oe.eq(Repl(~ResetSignal(), len(self.cs_oe))),
            self.bitbang_o.eq(self.d_i[1]),
        ]
        return m

def sim():
    from qspi_model import QspiModel
    m = Module()
    model = QspiModel()
    m.submodules.spi = spi = QspiMem()
    sim = Simulator(m)
    sim.add_clock(1e-6)
    def process():
        yield spi.sys_cfg.eq(0)
        yield spi.pad_count.eq(0x88)
        yield spi.max_burst.eq(0x10)
        yield spi.bitbang_i.eq(0)
        yield spi.data_bus.adr.eq(0x0A5A5A)
        yield spi.data_bus.sel.eq(1)
        yield spi.data_bus.we.eq(0)
        yield spi.data_bus.stb.eq(1)
        yield spi.data_bus.cyc.eq(1)
        for i in range(200):
            if (yield spi.data_bus.ack):
                yield spi.data_bus.stb.eq(0)
                yield spi.data_bus.cyc.eq(0)
            yield spi.d_i.eq(model.tick((yield spi.clk_o), (yield spi.cs_o), (yield spi.d_o)))
            yield
    sim.add_sync_process(process)
    with sim.write_vcd("qspi.vcd", "qspi.gtkw"):
        sim.run()

if __name__ == '__main__':
    sim()
