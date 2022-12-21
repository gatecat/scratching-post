shell cp sky130_fpga_bitmux.gds template_sky
gds read sky130_fpga_bitmux.gds
load sky130_fpga_routebuf
lef write sky130_fpga_routebuf.mag.lef
shell python3 -m bitcell_gen.patch_lef_sky130 sky130_fpga_routebuf.mag.lef template_sky/sky130_fpga_routebuf.lef
load sky130_fpga_bitmux
lef write sky130_fpga_bitmux.mag.lef
shell python3 -m bitcell_gen.patch_lef_sky130 sky130_fpga_bitmux.mag.lef template_sky/sky130_fpga_bitmux.lef
exit
