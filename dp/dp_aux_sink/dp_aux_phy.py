from amaranth import *
from amaranth.lib.cdc import FFSynchronizer
from amaranth.sim import Simulator, Delay, Settle, Passive

class DPAuxPhy(Elaboratable):
    def __init__(self, sys_clk_freq=48):
        self.sys_clk_freq = sys_clk_freq
        self.aux_i = Signal()
        self.aux_o = Signal()
        self.aux_oe = Signal()

        self.data_out = Signal(8)
        self.rx_strobe = Signal()
        self.stop_out = Signal()
        self.rx_idle = Signal()

        self.tx_begin = Signal()
        self.data_in = Signal(8)
        self.tx_valid = Signal()
        self.tx_ack = Signal()
        self.tx_busy = Signal()

    def elaborate(self, platform):
        m = Module()
        # Manchester receiver
        #  - Input synchronisation
        aux_i_sync = Signal()
        m.submodules += FFSynchronizer(i=self.aux_i, o=aux_i_sync)
        rx_sr = Signal(8)
        rx_bit_count = Signal(3)

        # Reference: https://www.infineon.com/dgdl/Infineon-AN2358_Manchester_Decoder_Using_PSoC_1-ApplicationNotes-v06_00-EN.pdf
        data_xor = Signal()
        data_xor_last = Signal()
        m.d.comb += data_xor.eq(aux_i_sync ^ rx_sr[0])
        m.d.sync += data_xor_last.eq(data_xor)

        # Sample timer
        T_samp = ((self.sys_clk_freq * 3) // 4) - 1
        T_stop = ((self.sys_clk_freq * 6) // 4) - 1
        T_stop_max = ((self.sys_clk_freq * 12) // 4) - 1

        T_timeout = (self.sys_clk_freq * 4) - 1
        samp_ctr = Signal(range(T_timeout + 1))

        m.d.sync += [
            self.stop_out.eq(0),
            self.rx_idle.eq(0),
            self.rx_strobe.eq(0),
        ]

        with m.If(data_xor & ~data_xor_last):
            with m.If(samp_ctr >= T_stop):
                # after a stop, we're already at the start of a bit
                m.d.sync += [
                    samp_ctr.eq(T_samp),
                    rx_bit_count.eq(0),
                ]
                with m.If(samp_ctr < T_stop_max):
                    m.d.sync += self.stop_out.eq(1)
            with m.Else():
                m.d.sync += samp_ctr.eq(0)
        with m.Elif(samp_ctr < T_timeout):
            m.d.sync += samp_ctr.eq(samp_ctr + 1)
        with m.Else():
            m.d.sync += self.rx_idle.eq(1)
        with m.If(samp_ctr == T_samp):
            m.d.sync += [
                rx_sr.eq(Cat(aux_i_sync, rx_sr[:-1])),
                Cat(rx_bit_count, self.rx_strobe).eq(rx_bit_count + 1),
            ]

        m.d.comb += self.data_out.eq(rx_sr)

        # Manchester transmitter
        tx_strobe = Signal()
        tx_half_strobe = Signal()
        tx_div = Signal(range(self.sys_clk_freq))
        tx_bit_count = Signal(8)
        tx_sr = Signal(8)
        tx_override = Signal()

        m.d.sync += [
            tx_strobe.eq(0),
            tx_half_strobe.eq(0),
        ]

        with m.If(tx_div == 0):
            m.d.sync += [
                tx_div.eq(self.sys_clk_freq - 1),
                tx_strobe.eq(1),
            ]
        with m.Else():
            with m.If(tx_div == ((self.sys_clk_freq // 2) - 1)):
                m.d.sync += tx_half_strobe.eq(1)
            m.d.sync += tx_div.eq(tx_div - 1)

        # transmit
        with m.If(tx_bit_count > 0):
            with m.If(tx_strobe):
                m.d.sync += [
                    self.aux_o.eq(tx_sr[-1]),
                    tx_sr.eq(Cat(tx_sr[-1], tx_sr[:-1])),
                    tx_bit_count.eq(tx_bit_count - 1),
                ]
            with m.If(tx_half_strobe & ~tx_override):
                m.d.sync += self.aux_o.eq(~self.aux_o)
        with m.FSM() as fsm:
            with m.State("IDLE"):
                m.d.sync += [
                    self.aux_oe.eq(0),
                    tx_override.eq(0),
                    tx_bit_count.eq(0),
                ]
                with m.If(tx_strobe & self.tx_begin):
                    m.d.sync += self.aux_oe.eq(1)
                    m.next = "BEGIN"
            with m.State("BEGIN"):
                with m.If(tx_strobe):
                    m.d.sync += [
                        tx_sr.eq(0),
                        tx_bit_count.eq(26) # send 26 zeros
                    ]
                    m.next = "PRECHARGE_SYNC"
            with m.State("PRECHARGE_SYNC"):
                with m.If(tx_strobe & (tx_bit_count == 1)):
                    m.d.sync += [
                        tx_bit_count.eq(4),
                        tx_sr.eq(0b11000000),
                        tx_override.eq(1)
                    ]
                    m.next = "SYNC_END"
            with m.State("SYNC_END"):
                pass
            m.d.comb += self.tx_busy.eq(~fsm.ongoing("IDLE"))
        return m

def sim_rx():
    # Test pattern
    pat = "0" * 10 # bus idle
    pat += "01" * 26 # initial sync
    pat += "11110000" # SYNC end
    pat += "".join("10" if x == "1" else "01" for x in "1010010101011100") # data
    pat += "11110000" # data end
    pat += "0" * 10 # bus idle

    sys_clk_freq = 48
    m = Module()
    m.submodules.phy = phy = DPAuxPhy(sys_clk_freq=sys_clk_freq)
    sim = Simulator(m)
    sim.add_clock(1e-6 / sys_clk_freq) # 48MHz

    def process():
        for bit in pat:
            yield phy.aux_i.eq(int(bit))
            yield Delay(0.5e-6) # half bitrate (Manchester)

    def checker():
        got_sync = False
        got_stop = False
        byte_idx = 0
        stop_count = 0 
        yield Passive()
        while True:
            yield
            if (yield phy.rx_strobe):
                dout = (yield phy.data_out)
                if dout == 0x00 or dout == 0xFF:
                    got_sync = True
                if got_stop:
                    if byte_idx == 0: assert dout == 0xA5, dout
                    if byte_idx == 1: assert dout == 0x5C, dout
                    byte_idx += 1
            if (yield phy.stop_out):
                assert got_sync # assert a sync before the first stop
                if got_stop: # second stop
                    print(f"Received {byte_idx} bytes!")
                    assert byte_idx >= 2
                got_stop = True

    sim.add_process(process)
    sim.add_sync_process(checker)
    with sim.write_vcd("phy_rx.vcd", "phy_rx.gtkw", traces=[phy.aux_i, phy.aux_o]):
        sim.run()

def sim_tx():
    sys_clk_freq = 48
    m = Module()
    m.submodules.phy = phy = DPAuxPhy(sys_clk_freq=sys_clk_freq)
    sim = Simulator(m)
    sim.add_clock(1e-6 / sys_clk_freq) # 48MHz
    def process():
        for i in range(4): yield
        yield phy.tx_begin.eq(1)
        while (yield phy.tx_busy) == 0:
            yield
        yield phy.tx_begin.eq(0)
        for i in range(sys_clk_freq * 100): yield
    sim.add_sync_process(process)
    with sim.write_vcd("phy_tx.vcd", "phy_tx.gtkw", traces=[phy.aux_i, phy.aux_o]):
        sim.run()

if __name__ == '__main__':
    # sim_rx()
    sim_tx()
