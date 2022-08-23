#!/usr/bin/env bash
set -ex
iverilog -DFUNCTIONAL -DUNIT_DELAY=\#0 -s lutram_tb -o lutram.vvp lutram_sky130.v lutram_tb.v
vvp lutram.vvp
