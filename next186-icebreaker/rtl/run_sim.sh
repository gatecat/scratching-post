#!/usr/bin/env bash
set -ex
verilator -j 7 --cc --exe --build --trace -Wno-pinmissing -Wno-caseincomplete -Wno-UNOPTFLAT -Wno-MULTIDRIVEN -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC --timing --top-module testbench --main Next186/*.v top.v testbench.v
./obj_dir/Vtestbench
