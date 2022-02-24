from amaranth import *
from amaranth.lib.cdc import FFSynchronizer
from amaranth.sim import Simulator, Delay, Settle, Passive

class DPAuxPacketHandler(Elaboratable):
    def __init__(self):
        self.sys_clk_freq = sys_clk_freq

        self.rx_data_in = Signal(8)
        self.rx_strobe = Signal()
        self.rx_stop_in = Signal()
        self.rx_idle_in = Signal()

        self.tx_begin = Signal()
        self.tx_data_out = Signal(8)
        self.tx_valid = Signal()
        self.tx_ack = Signal()
        self.tx_busy = Signal()

    def elaborate(self, platform):
        m = Module()
        # Command header
        header = Signal(24)
        cmd = header[-4:]
        addr = header[:-4]
        is_i2c = ~cmd[3]
        mot = cmd[2]
        req = cmd[1:0]

        REQ_WR   = 0b00
        REQ_RD   = 0b01
        REQ_WSUR = 0b10

        nat_reply = Signal(2)
        i2c_reply = Signal(2)
        reply_hdr = Cat(nat_reply, i2c_reply, C(0, 4))
