#!/usr/bin/env bash
set -ex
BITSTREAM=$HOME/test/fab/inv.bit
PRJ=$HOME/FABulous-refactor/test_prj
MAX_BITWORDS=4096

FAB_FILES=$(awk "{print \"$PRJ/\"\$0}" files.f | tr '\n' ' ')
iverilog $FAB_FILES fab_tb.v -s fab_tb -o fab_tb.vvp
python3 makehex.py $BITSTREAM $MAX_BITWORDS bitstream.hex
vvp fab_tb.vvp
