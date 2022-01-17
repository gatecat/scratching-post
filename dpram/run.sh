#!/usr/bin/env bash

DESIGN=${1%.v}
set -ex
iverilog -o ${DESIGN}.vvp -s testbench ${DESIGN}.v tech.v
vvp ${DESIGN}.vvp
