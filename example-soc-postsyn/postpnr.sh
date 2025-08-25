#!/usr/bin/env bash
set -ex
PDK_VERILOG=/home/gatecat/sky130/sky130A/libs.ref/sky130_fd_sc_hd/verilog
CVC64=/home/gatecat/open-src-cvc/src/cvc64

$CVC64 +define+FUNCTIONAL +dump2fst +fst+parallel=on -o postpnr $PDK_VERILOG/primitives.v $PDK_VERILOG/sky130_fd_sc_hd.v 6_final.v spiflash.v testbench.v
