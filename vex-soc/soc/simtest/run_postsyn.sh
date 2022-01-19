#!/usr/bin/env bash
set -ex
riscv64-linux-gnu-objcopy -O verilog ../../software/blink.elf firmware.hex
yosys -p "write_verilog -norename ../../build/fpga/top_postsyn.v" ../../build/fpga/top.json
iverilog -DPOSTSYN -I/home/gatecat/yosys/techlibs/nexus -o testbench.vvp -s testbench spiflash.v simtest.v ../../build/fpga/top_postsyn.v /home/gatecat/yosys/techlibs/nexus/cells_sim.v
vvp testbench.vvp
