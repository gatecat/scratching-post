#!/usr/bin/env bash
set -ex
BITSTREAM=$HOME/test/fab/inv.bit
PRJ=$HOME/FABulous-refactor/test_prj

FAB_FILES=$(awk "{print \"$PRJ/\"\$0}" files.f | tr '\n' ' ')
iverilog $FAB_FILES fab_tb.v -s fab_tb -o fab_tb.vvp
