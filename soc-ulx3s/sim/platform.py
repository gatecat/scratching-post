import argparse, sys, os
from pathlib import Path

from amaranth import *
from amaranth.back import rtlil

class SimPlatform():
    def __init__(self):
        self.is_sim = True
        self.build_dir = "build/sim"
        self.extra_files = set()
        self.clk = Signal()
        self.rst = Signal()
        self.sim_boxes = dict()

    def add_file(self, filename, content):
        self.extra_files.add(filename)

    def add_model(self, inst_type, rec, edge_det=[]):
        conns = dict(a_keep=True)
        def is_model_out(pin):
            assert field.endswith("_o") or field.endswith("_oe") or field.endswith("_i"), field
            return field.endswith("_i")
        for field, _, _ in rec.layout:
            if is_model_out(field):
                conns[f"o_{field}"] = getattr(rec, field)
            else:
                conns[f"i_{field}"] = getattr(rec, field)
        if inst_type not in self.sim_boxes:
            box =  'attribute \\blackbox 1\n'
            box += 'attribute \\cxxrtl_blackbox 1\n'
            box += 'attribute \\keep 1\n'
            box += f'module \\{inst_type}\n'
            for i, (field, width, _) in enumerate(rec.layout):
                if field in edge_det:
                    box += '  attribute \\cxxrtl_edge "a"\n'
                box += f'  wire width {width} {"output" if is_model_out(field) else "input"} {i} \\{field}\n'
            box += 'end\n\n'
            self.sim_boxes[inst_type] = box
        return Instance(inst_type, **conns)

    def build(self, e):
        Path(self.build_dir).mkdir(parents=True, exist_ok=True)

        output = rtlil.convert(e, name="sim_top", ports=[self.clk, self.rst], platform=self)

        top_rtlil = Path(self.build_dir) / "sim_top.il"
        with open(top_rtlil, "w") as f:
            for box_content in self.sim_boxes.values():
                f.write(box_content)
            f.write(output)
