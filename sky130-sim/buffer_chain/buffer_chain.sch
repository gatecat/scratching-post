v {xschem version=3.1.0 file_version=1.2 }
G {}
K {}
V {}
S {}
E {}
C {devices/code_shown.sym} 370 -110 0 0 {name=SPICE only_toplevel=false value=".lib /usr/local/share/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice tt
.include /usr/local/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice
.tran 0.1n 1u
.save all
vvcc vcc 0 dc 1.8
vvss vss 0 0
"}
C {devices/lab_pin.sym} -370 -400 0 0 {name=l2 sig_type=std_logic lab=xxx}
