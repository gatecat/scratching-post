#!/usr/bin/env bash
set -ex
yosys -p "synth_ice40 -top top -json top.json" Next186/*.v top.v
nextpnr-ice40 --json top.json --pcf icebreaker.pcf --up5k --package sg48 --asc top.asc --timing-allow-fail
icepack top.asc top.bin
iceprog top.bin
