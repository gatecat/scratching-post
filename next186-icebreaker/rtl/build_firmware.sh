#!/usr/bin/env bash
set -ex
nasm -o firmware.bin firmware.s
objcopy -I binary -O verilog --verilog-data-width 4  firmware.bin rom.hex
