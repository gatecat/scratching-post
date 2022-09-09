#!/usr/bin/env bash
set -ex
BITSTREAM=$HOME/test/fab/inv.bit
PRJ=$HOME/FABulous-refactor/test_prj

FAB_FILES=$(ls $PRJ/Fabric/*.v)
TILE_FILES=$(ls $PRJ/Tile/**/*.v)
iverilog $FAB_FILES $TILE_FILES fab_tb.v -s fab_tb -o fab_tb.vvp