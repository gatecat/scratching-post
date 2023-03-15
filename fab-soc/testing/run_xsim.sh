#!/usr/bin/env bash
set -ex
xvlog postsyn_tb.v ../../../build/xilinx_zcu104/postsyn_sim.v /opt/Xilinx/Vivado/2022.1/data/verilog/src/glbl.v
xelab --debug wave xilinx_zcu104_tb glbl -s zcu104_postsyn_sim -L unisims_ver -L unimacro_ver
xsim -wdb out.wdb -R zcu104_postsyn_sim

