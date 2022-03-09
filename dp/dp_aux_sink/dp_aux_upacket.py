from amaranth import *
from amaranth.lib.cdc import FFSynchronizer
from amaranth.sim import Simulator, Delay, Settle, Passive

class DPAuxPacketHandler(Elaboratable):
    def __init__(self):
        # PHY interface
        self.rx_data_in  = Signal(8)
        self.rx_strobe   = Signal()
        self.rx_stop_in  = Signal()
        self.rx_idle_in  = Signal()

        self.tx_begin    = Signal()
        self.tx_data_out = Signal(8)
        self.tx_valid    = Signal()
        self.tx_ack      = Signal()
        self.tx_busy     = Signal()

        # Native register interface
        self.reg_adr     = Signal(24)
        self.reg_w_data  = Signal(8)
        self.reg_r_data  = Signal(8)
        self.reg_w_stb   = Signal()
        self.reg_r_stb   = Signal()

        # I2C interface
        self.i2c_active  = Signal()
        self.i2c_adr     = Signal(8)
        self.i2c_w_data  = Signal(8)
        self.i2c_r_data  = Signal(8)
        self.i2c_w_stb   = Signal()
        self.i2c_r_stb   = Signal()
        self.i2c_ack     = Signal()

    def elaborate(self, platform):
        m = Module()
        # Command header
        header = Signal(24)
        cmd = header[-4:]
        addr = header[:-4]
        is_i2c = ~cmd[3]
        mot = cmd[2]
        req = cmd[:2]

        REQ_WR   = 0b00
        REQ_RD   = 0b01
        REQ_WSUR = 0b10

        nat_reply = Signal(2)
        i2c_reply = Signal(2)
        reply_hdr = Cat(nat_reply, i2c_reply, C(0, 4))

        byte_count = Signal(5)
        length = Signal(8)
        with m.If(self.rx_idle_in):
            m.d.sync += byte_count.eq(0)
        with m.Elif(self.rx_strobe):
            m.d.sync += [
                byte_count.eq(byte_count + 1),
            ]

        m.d.sync += [
            self.reg_r_stb.eq(0),
            self.reg_w_stb.eq(0),
            self.i2c_r_stb.eq(0),
            self.i2c_w_stb.eq(0),
        ]

        with m.FSM() as fsm:
            with m.State("IDLE"):
                with m.If(~self.rx_idle_in):
                    m.next = "SYNC"
            with m.State("SYNC"):
                with m.If(self.rx_idle_in):
                    m.next = "IDLE"
                with m.Elif(self.rx_stop_in):
                    m.d.sync += byte_count.eq(0)
                    m.next = "RX_HEADER"
            with m.State("RX_HEADER"):
                with m.If(self.rx_idle_in):
                    m.next = "IDLE"
                with m.If(self.rx_strobe):
                    m.d.sync += header.eq(Cat(self.rx_data_in, header[:-8]))
                    with m.If(byte_count == 2):
                        m.next = "GET_LENGTH"
                        m.d.sync += byte_count.eq(0)
            with m.State("GET_LENGTH"):
                # Update address latch from header
                with m.If(is_i2c):
                    pass # TODO
                with m.Else():
                    self.reg_adr.eq(addr)
                # Determine next state
                with m.If(self.rx_idle_in): # aborted early
                    m.next = "IDLE"
                with m.Elif(self.rx_stop_in): # no length field
                    m.d.sync += length.eq(0)
                    m.next = "BEGIN_REPLY"
                with m.Elif(self.rx_strobe): # length field
                    m.d.sync += [
                        length.eq(self.rx_data_in),
                        byte_count.eq(0),
                    ]
                    m.next = "GOT_LENGTH"
            with m.State("GOT_LENGTH"):
                with m.If((req == REQ_WSUR) | (req == REQ_RD) | (length == 0)):
                    with m.If(self.rx_idle_in):
                        m.next = "BEGIN_REPLY"
                with m.Else():
                    m.next = "RECV_DATA"
            with m.State("RECV_DATA"):
                with m.If(self.rx_idle_in):
                    m.next = "BEGIN_REPLY"
                with m.Elif(self.rx_strobe):
                    with m.If(is_i2c):
                        pass # TODO
                    with m.Else():
                        self.reg_w_data.eq(self.rx_data_in)
                        self.reg_w_stb.eq(1)
            with m.State("BEGIN_REPLY"):
                pass

        # Increment address latch one cycle later
        with m.If(self.reg_w_stb | self.reg_r_stb):
            m.d.sync += self.reg_adr.eq(self.reg_adr + 1)

        return m



def sim_reg_read():
    rx_data = [
        0b10010000, # native read; address: 0x0
        0b00001100, # address: 0x0C
        0b10100111, # address: 0xA7
        0b00000010, # length: 2
    ]

    sys_clk_freq = 48
    m = Module()
    m.submodules.ph = ph = DPAuxPacketHandler()
    sim = Simulator(m)
    sim.add_clock(1e-6 / sys_clk_freq) # 48MHz

    def process():
        def send(b):
            for j in range(40): yield
            yield ph.rx_data_in.eq(b)
            yield ph.rx_strobe.eq(1)
            yield
            yield ph.rx_strobe.eq(0)
            for j in range(20): yield
        def stop():
            yield ph.rx_stop_in.eq(1)
            yield
            yield ph.rx_stop_in.eq(0)
            yield
        yield ph.rx_idle_in.eq(1)
        for i in range(10): yield
        yield ph.rx_idle_in.eq(0)
        for i in range(4):
            for x in send(0): yield x # SYNC
        for x in stop(): yield x
        for b in rx_data:
            for x in send(b): yield x
        for x in stop(): yield x
        for i in range(10): yield
        yield ph.rx_idle_in.eq(1)

    sim.add_sync_process(process)
    with sim.write_vcd("upacket.vcd", "upacket.gtkw"):
        sim.run()

if __name__ == '__main__':
    sim_reg_read()

