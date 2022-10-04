from ..fabric.tiletype import *
from ..fabric.bel import *
from ..fabric.fabric import *
from itertools import product

base_width = 12
sig_width = base_width + 1 # +1 for the valid signal


class CgraElem(Bel):
    def __init__(self, name, prefix, tech, standalone=False):
        super().__init__(name, "CgraElem", prefix)
        self.a = Signal(sig_width)
        self.b = Signal(sig_width)
        self.q = Signal(sig_width)
        self.clr = Signal()

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

    def elaborate(self, m):
        m = Module()
        a_q = Signal(sig_width)
        b_q = Signal(sig_width)
        with m.If(self.clr):
            m.d.sync += [
                a_q.eq(0),
                b_q.eq(0),
            ]
        with m.Else():
            m.d.sync += [
                a_q.eq(self.a),
                b_q.eq(self.b),
            ]
        a_i = Signal(sig_width)
        b_i = Signal(sig_width)
        m.d.comb += [
            a_i.eq(Mux(self._a_reg, self.a, a_q)),
            b_i.eq(Mux(self._b_reg, self.b, b_q)),
        ]

        a_data = Signal(signed(base_width))
        a_valid = Signal()
        b_data = Signal(signed(base_width))
        b_valid = Signal()

        m.d.comb += [
            a_data.eq(a_i[:base_width]),
            a_valid.eq(a_i[-1]),
            b_data.eq(Mux(self._b_const, b_i[:base_width], self._const_val)),
            b_valid.eq(Mux(self._b_const, b_i[-1], 1)),
        ]

        mult_res = Signal(signed(base_width))
        add_a = Signal(signed(base_width))
        add_b = Signal(signed(base_width))
        add_res = Signal(signed(base_width))
        res_d = Signal(signed(base_width))
        res_q = Signal(signed(base_width))
        valid_d = Signal()
        valid_q = Signal()

        m.d.comb += [
            mult_res.eq(a_data * b_data),
            add_a.eq(Mux(self._mult_byp, mult_res, a_data)),
            add_b.eq(Mux(self._add_acc, b_data, res_q)),
            add_res.eq(add_a + add_b),
            res_d.eq(Mux(self._add_byp, add_res, mult_res)),
            valid_d.eq(Mux(self._mult_byp & self._add_acc, a_valid & b_valid, a_valid)),
        ]

        with m.If(self.clr):
            m.d.sync += [
                res_q.eq(0),
                valid_q.eq(0),
            ]
        with m.Else():
            m.d.sync += [
                res_q.eq(res_d),
                valid_q.eq(valid_d),
            ]

        m.d.comb += self.q.eq(Cat(res_q, valid_q))
        if self.standalone:
            m.d.comb += self.cfg.sigs().eq(self.mode)
        return m

if __name__ == '__main__':
    import sys
    from amaranth.back import verilog
    from ..tech.base import BaseTech

    tech = BaseTech()
    elem = CgraElem("CgraElem", "A", tech, standalone=True)
    with open(sys.argv[1], "w") as f:
        f.write(verilog.convert(elem, name="cgra_mul_tile", ports=[elem.clr, elem.mode, elem.a, elem.b, elem.q]))



