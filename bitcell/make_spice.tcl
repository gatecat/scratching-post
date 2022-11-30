gds read gf180mcu_fpga_bitmux.gds
load gf180mcu_fpga_bitmux

box values 0um 0um 0.1um 0.1um -edit
label VPW east pwell

box values 0um 4um 0.1um 4.1um -edit
label VNW east nwell

select cell

port makeall
port renumber

extract
ext2spice
save gf180mcu_fpga_bitmux.mag
exit

