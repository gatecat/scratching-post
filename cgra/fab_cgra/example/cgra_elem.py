from ..fabric.tiletype import *
from ..fabric.bel import *
from ..fabric.fabric import *
from itertools import product


class CgraElem(Bel):
    def __init__(self, name, prefix, tech, base_width, standalone=False):
        super().__init__(name, "CgraElem", prefix)
        self.base_width = base_width
        sig_width = self.base_width + 1
        self.A = Signal(sig_width)
        self.B = Signal(sig_width)
        self.Q = Signal(sig_width)
        self.CLR = Signal()

        self._a_reg = self.cfg.bit("A_REG")
        self._b_reg = self.cfg.bit("B_REG")
        self._const_val = self.cfg.word("CONST_VAL", base_width)
        self._b_const = self.cfg.bit("B_CONST")

        self._mult_byp = self.cfg.bit("MULT_BYP")
        self._add_acc = self.cfg.bit("ADD_ACC")
        self._add_byp = self.cfg.bit("ADD_BYP")

        self.standalone = standalone
        if standalone:
            self.mode = Signal(self.cfg.count())

    def get_ports(self):
        return [
            PortSpec(name="A", dir=PortDir.IN, shape=self.base_width+1),
            PortSpec(name="B", dir=PortDir.IN, shape=self.base_width+1),
            PortSpec(name="CLR", dir=PortDir.IN, shape=self.base_width+1),
            PortSpec(name="Q", dir=PortDir.OUT, shape=self.base_width+1),
        ]

    def elaborate(self, m):
        sig_width = self.base_width + 1
        m = Module()
        a_q = Signal(sig_width)
        b_q = Signal(sig_width)
        with m.If(self.CLR):
            m.d.sync += [
                a_q.eq(0),
                b_q.eq(0),
            ]
        with m.Else():
            m.d.sync += [
                a_q.eq(self.A),
                b_q.eq(self.B),
            ]
        a_i = Signal(sig_width)
        b_i = Signal(sig_width)
        m.d.comb += [
            a_i.eq(Mux(self._a_reg, a_q, self.A)),
            b_i.eq(Mux(self._b_reg, b_q, self.B)),
        ]

        a_data = Signal(signed(self.base_width))
        a_valid = Signal()
        b_data = Signal(signed(self.base_width))
        b_valid = Signal()

        m.d.comb += [
            a_data.eq(a_i[:self.base_width]),
            a_valid.eq(a_i[-1]),
            b_data.eq(Mux(self._b_const, self._const_val, b_i[:self.base_width])),
            b_valid.eq(Mux(self._b_const, 1, b_i[-1])),
        ]

        mult_res = Signal(signed(self.base_width))
        add_a = Signal(signed(self.base_width))
        add_b = Signal(signed(self.base_width))
        add_res = Signal(signed(self.base_width))
        res_d = Signal(signed(self.base_width))
        res_q = Signal(signed(self.base_width))
        valid_d = Signal()
        valid_q = Signal()

        m.d.comb += [
            mult_res.eq(a_data * b_data),
            add_a.eq(Mux(self._mult_byp, a_data, mult_res)),
            add_b.eq(Mux(self._add_acc, res_q, mult_res)),
            add_res.eq(add_a + add_b),
            res_d.eq(Mux(self._add_byp, mult_res, add_res)),
            valid_d.eq(Mux(self._mult_byp & self._add_acc, a_valid, a_valid & b_valid)),
        ]

        with m.If(self.CLR):
            m.d.sync += [
                res_q.eq(0),
                valid_q.eq(0),
            ]
        with m.Else():
            m.d.sync += [
                res_q.eq(res_d),
                valid_q.eq(valid_d),
            ]

        m.d.comb += self.Q.eq(Cat(res_q, valid_q))
        if self.standalone:
            m.d.comb += self.cfg.sigs().eq(self.mode)
        return m

if __name__ == '__main__':
    import sys
    from amaranth.back import verilog
    from ..tech.base import BaseTech

    tech = BaseTech()
    elem = CgraElem("CgraElem", "A", tech, base_width=12, standalone=True)
    with open(sys.argv[1], "w") as f:
        f.write(verilog.convert(elem, name="cgra_mul_tile", ports=[elem.clr, elem.mode, elem.a, elem.b, elem.q]))



