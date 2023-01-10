#!/usr/bin/env bash

SYNTH_TCL=${HOME}/FABulous-refactor/nextpnr/fabulous/synth/synth_fabulous.tcl
BIT_GEN=${HOME}/FABulous-refactor/nextpnr/fabulous/fab_arch/bit_gen.py

DESIGN=${1%.v}
SCRIPT_DIR=$( dirname "${BASH_SOURCE[0]}" )

set -ex
yosys -qp "tcl $SYNTH_TCL 4 top_wrapper ${DESIGN}.json" ${DESIGN}.v ${SCRIPT_DIR}/top_wrapper.v
yosys -p stat ${DESIGN}.json

FAB_ROOT=${HOME}/FABulous-refactor/test_prj nextpnr-generic --uarch fabulous --json ${DESIGN}.json -o fasm=${DESIGN}_des.fasm
# python3 ${BIT_GEN} -genBitstream test_design/${DESIGN}_des.fasm ../../fabric_generator/npnroutput/meta_data.txt test_design/${DESIGN}.bin
