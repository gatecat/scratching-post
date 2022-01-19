from amaranth import *
from amaranth.utils import log2_int

from amaranth_soc import wishbone

from .peripheral import Peripheral

class Vexriscv():
    def __init__(self):
        self.dbus = wishbone.Interface(addr_width=29,
                                      data_width=32, granularity=8, features={"cti", "bte"}) 
        self.ibus = wishbone.Interface(addr_width=29,
                                      data_width=32, granularity=8, features={"cti", "bte"})
        self.timer_irq = Signal()
        self.software_irq = Signal()
        self.ext_irq = Signal(32)
        self.debug_rst = Signal()
        self.jtag_tms = Signal()
        self.jtag_tdi = Signal()
        self.jtag_tdo = Signal()
        self.jtag_tck = Signal()
        self.size = 2**24

    def elaborate(self, platform):
        m.submodules.vex = Instance(
            "VexRiscv",
            i_timerInterrupt=self.timer_irq,
            i_softwareInterrupt=self.software_irq,
            i_externalInterruptArray=self.ext_irq,
            o_debug_resetOut=self.debug_rst,

            o_iBusWishbone_CYC=self.ibus.cyc,
            o_iBusWishbone_STB=self.ibus.stb,
            i_iBusWishbone_ACK=self.ibus.ack,
            o_iBusWishbone_WE=self.ibus.we,
            o_iBusWishbone_ADR=self.ibus.adr,
            i_iBusWishbone_DAT_MISO=self.ibus.dat_r,
            o_iBusWishbone_DAT_MOSI=self.ibus.dat_w,
            o_iBusWishbone_SEL=self.ibus.sel,
            i_iBusWishbone_ERR=0,
            o_iBusWishbone_CTI=self.ibus.cti,
            o_iBusWishbone_BTE=self.ibus.bte,

            o_dBusWishbone_CYC=self.dbus.cyc,
            o_dBusWishbone_STB=self.dbus.stb,
            i_dBusWishbone_ACK=self.dbus.ack,
            o_dBusWishbone_WE=self.dbus.we,
            o_dBusWishbone_ADR=self.dbus.adr,
            i_dBusWishbone_DAT_MISO=self.dbus.dat_r,
            o_dBusWishbone_DAT_MOSI=self.dbus.dat_w,
            o_dBusWishbone_SEL=self.dbus.sel,
            i_dBusWishbone_ERR=0,
            o_dBusWishbone_CTI=self.dbus.cti,
            o_dBusWishbone_BTE=self.dbus.bte,

            i_jtag_tms=self.jtag_tms,
            i_jtag_tdi=self.jtag_tdi,
            o_jtag_tdo=self.jtag_tdo,
            i_jtag_tck=self.jtag_tck,

            i_clk=ClockSignal(),
            i_reset=ResetSignal(),
            i_debugReset=ResetSignal(),
        )
        return m
