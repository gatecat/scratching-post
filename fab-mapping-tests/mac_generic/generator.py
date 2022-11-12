import sys
import argparse
import pathlib

prim_name = "MULADDB"
wrap_name = "MULADDB_WRAP"

class MacGenerator:
    def __init__(self, a_width, b_width, c_width):
        self.a_width = a_width
        self.b_width = b_width
        self.c_width = c_width
        self.with_acc = self.c_width > 0
        self.out_width = max(self.a_width + self.b_width, self.c_width)
        if self.with_acc:
            self.params = ["A_reg", "B_reg", "C_reg", "ACC", "signExtension", "ACCout"]
        else:
            self.params = ["A_reg", "B_reg", "signExtension"]
    def generate_prim(self, for_sim, filename):
        with open(filename, "w") as f:
            # the generated verilog has to comply with strict rules as FABulous is currently using regexes to parse :/
            # top level port list
            ports = []
            for a in range(self.a_width-1, -1, -1):
                ports.append(("input", f"A{a}"))
            for b in range(self.b_width-1, -1, -1):
                ports.append(("input", f"B{b}"))
            if self.with_acc:
                for c in range(self.c_width-1, -1, -1):
                    ports.append(("input", f"C{c}"))
            for b in range(self.out_width-1, -1, -1):
                ports.append(("output", f"Q{b}"))
            if self.with_acc:
                ports.append(("input", "clr"))
            if for_sim:
                ports.append(("input", "CLK"))
            else:
                ports.append(("input", "UserCLK", "// EXTERNAL // SHARED_PORT"))
                ports.append(("input [NoConfigBits-1:0]", "ConfigBits"))
            print(f"module {prim_name} ({', '.join(x[1] for x in ports)});", file=f)
            # in sim/synth blackbox parameters are separate
            # in the underlying hardware, there is no concept of parameters and they are passed as a bitvector wire instead
            if for_sim:
                for p in self.params:
                    print(f"    parameter {p} = 1'b0;", file=f)
            else:
                print(f"    parameter NoConfigBits = {len(self.params)};", file=f)
            for p in ports:
                print(f"    {p[0]} {p[1]};{' ' + p[2] if len(p) > 2 else ''}", file=f)
            if not for_sim:
                for i, p in enumerate(self.params):
                    print(f"    wire {p} = ConfigBits[{i}];", file=f)
            operands = [("A", self.a_width), ("B", self.b_width)]
            if self.with_acc:
                operands.append(("C", self.c_width))
            for op, w in operands:
                print(f"    wire [{w-1}:0] {op}, OP{op};", file=f)
                print(f"    reg [{w-1}:0] {op}_q;", file=f)
                print(f"    assign {op} = {{{', '.join(f'{op}{i}' for i in range(w-1,-1,-1))}}};", file=f)
                print(f"    assign OP{op} = {op}_reg ? {op}_q : {op};", file=f)
                print("", file=f)
            print("endmodule", file=f)
    def generate_wrap(self, filename):
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='a_width', type=int, required=True)
    parser.add_argument('-b', dest='b_width', type=int, required=True)
    parser.add_argument('-c', dest='c_width', type=int, default=0)
    parser.add_argument('-o', dest='out', type=str, required=True)

    args = parser.parse_args()
    pathlib.Path(args.out).mkdir(parents=True, exist_ok=True)
    gen = MacGenerator(a_width=args.a_width, b_width=args.b_width, c_width=args.c_width)
    gen.generate_prim(for_sim=False, filename=f"{args.out}/{prim_name}_bel.v")
    gen.generate_prim(for_sim=True, filename=f"{args.out}/{prim_name}_sim.v")
    gen.generate_wrap(filename=f"{args.out}/{prim_name}_wrap.v")

if __name__ == '__main__':
    main()