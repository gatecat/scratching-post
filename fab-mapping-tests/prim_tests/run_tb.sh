#!/usr/bin/env bash
set -ex
iverilog ../prims.v $1 -s testbench -o testbench.vvp
vvp testbench.vvp
