import argparse, sys, os
from pathlib import Path

from amaranth import *
from amaranth.back import rtlil

class SimPlatform():
    def __init__(self):
        self.is_sim = True
        self.build_dir = "build"
        self.extra_files = set()
        self.clk = Signal()
        self.rst = Signal()

    def add_file(self, filename, content):
        self.extra_files.add(filename)

    def build(self, e):
        Path(self.build_dir).mkdir(parents=True, exist_ok=True)

        output = rtlil.convert(e, name="sim_top", ports=[self.clk, self.rst], platform=self)

        top_rtlil = Path(self.build_dir) / "sim_top.il"
        with open(top_rtlil, "w") as f:
            f.write(output)
