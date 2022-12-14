#!/usr/bin/env bash
set -ex
mkdir -p testbench/work
python -m fab_cgra.example.cgra_tile work/cgra_tile.gen.v
python testbench/assemble.py work/cgra_tile.gen.v.features testbench/mul_and_route.cfg testbench/work/mul_and_route.bin
iverilog -o testbench/work/mul_and_route.vvp -s testbench work/cgra_tile.gen.v fab_cgra/tech/generic_lib.v testbench/cgra_tile_tb.v
vvp testbench/work/mul_and_route.vvp

