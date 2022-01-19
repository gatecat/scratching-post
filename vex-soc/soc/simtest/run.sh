#!/usr/bin/env bash
set -ex
riscv64-linux-gnu-objcopy -O verilog ../../software/blink.elf firmware.hex
iverilog -o testbench.vvp -s testbench spiflash.v simtest.v ../../build/fpga/top.v ../../cores/spimemio.v ../../verilog_gen/VexRiscvLinuxAsic.v
vvp testbench.vvp
