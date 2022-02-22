from amaranth import *
from amaranth.lib.cdc import FFSynchronizer
from amaranth.sim import Simulator, Delay, Settle

class DPAuxPhy(Elaboratable):
    def __init__(self, sys_clk_freq=48):
        self.sys_clk_freq = sys_clk_freq
        self.aux_i = Signal()
        self.aux_o = Signal()
        self.aux_oe = Signal()

    def elaborate(self, platform):
        m = Module()
        # Manchester receiver
        #  - Input synchronisation
        aux_i_sync = Signal()
        m.submodules += FFSynchronizer(i=self.aux_i, o=aux_i_sync)

        #  - Soft edge detection
        aux_i_last = Signal()
        m.d.sync += aux_i_last.eq(aux_i_sync)
        aux_i_edge = Signal()
        m.d.comb += aux_i_edge.eq(aux_i_sync ^ aux_i_last)

        #  - Sampling counter
        timeout_t = self.sys_clk_freq * 4 - 1
        stop_t =  ((self.sys_clk_freq * 6) // 4) - 1
        samp_ctr = Signal(range(timeout_t + 1))
        three_quarter_t = ((self.sys_clk_freq * 3) // 4) - 1
        with m.If(aux_i_edge & (samp_ctr > three_quarter_t)):
            # Only reset counter at beginning-of-bit transitions
            m.d.sync += samp_ctr.eq(0)
        with m.Elif(~samp_ctr.all()):
            m.d.sync += samp_ctr.eq(samp_ctr + 1)

        #  - Sampling
        bit_strobe = Signal()
        bit_ctr = Signal(8)
        out_sr = Signal(8)
        m.d.sync += bit_strobe.eq(0)
        with m.If(samp_ctr > stop_t):
            # 'STOP' condition (like end of sync)
            m.d.sync += [
                bit_ctr.eq(0),
                out_sr.eq(0),
            ]
        with m.Elif(samp_ctr == three_quarter_t):
            m.d.sync += [
                out_sr.eq(Cat(~aux_i_last, out_sr[:-1])),
                bit_strobe.eq(1),
            ]
        with m.Elif(samp_ctr == three_quarter_t + 1):
            m.d.sync += [
                bit_ctr.eq(bit_ctr + 1),
            ]
        return m # TODO

def sim():
    # Test pattern
    pat = "0" * 10 # bus idle
    pat += "01" * 26 # initial sync
    pat += "11110000" # SYNC end
    pat += "".join("10" if x == "1" else "01" for x in "1010010101011100") # data
    pat += "11110000" # data end

    sys_clk_freq = 48
    m = Module()
    m.submodules.phy = phy = DPAuxPhy(sys_clk_freq=sys_clk_freq)
    sim = Simulator(m)
    sim.add_clock(1e-6 / sys_clk_freq) # 48MHz

    def process():
        for bit in pat:
            yield phy.aux_i.eq(int(bit))
            yield Delay(0.5e-6) # half bitrate (Manchester)
    sim.add_process(process)
    with sim.write_vcd("phy.vcd", "phy.gtkw", traces=[phy.aux_i, phy.aux_o]):
        sim.run()

if __name__ == '__main__':
    sim()
