#!/usr/bin/env bash
set -ex
iverilog -s fpga_tb -o fpga.vvp fpga_tb.v fpga_top.v fpga_cells.v logic_cell.v
vvp fpga.vvp
