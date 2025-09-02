#!/usr/bin/env bash
set -ex
PDK_VERILOG=/home/gatecat/sky130/sky130A/libs.ref/sky130_fd_sc_hd/verilog

verilator -O3 --x-assign fast --x-initial fast --noassert -Wno-PINMISSING  --top-module sim_top --cc --exe --build -j 8 \
 -DFUNCTIONAL -DUNIT_DELAY  $PDK_VERILOG/primitives.v $PDK_VERILOG/sky130_fd_sc_hd.v  \
 1_synth.v verilator_wrapper.v \
 models/models.cc main.cc
