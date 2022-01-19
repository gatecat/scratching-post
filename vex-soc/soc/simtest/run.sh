#!/usr/bin/env bash
set -ex
riscv64-linux-gnu-objcopy -O verilog ../../software/bios.elf firmware.hex
iverilog -o testbench.vvp -s testbench spiflash.v simtest.v ../../build/fpga/top.v ../../cores/spimemio.v ../../verilog_gen/VexRiscvLinuxAsic.v /home/gatecat/test/S27KL0642.v
vvp testbench.vvp
