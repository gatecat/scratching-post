v {xschem version=3.1.0 file_version=1.2 }
G {}
K {}
V {}
S {}
E {}
N 120 -20 120 10 {
lab=GND}
N 290 -140 290 -110 {
lab=w1}
N 250 -140 290 -140 {
lab=w1}
N 290 -50 290 10 {
lab=GND}
N 450 -140 450 -110 {
lab=w2}
N 410 -140 450 -140 {
lab=w2}
N 450 -50 450 10 {
lab=GND}
N 620 -140 620 -110 {
lab=w3}
N 580 -140 620 -140 {
lab=w3}
N 620 -50 620 10 {
lab=GND}
N 790 -140 790 -110 {
lab=#net1}
N 750 -140 790 -140 {
lab=#net1}
N 790 -50 790 10 {
lab=GND}
N 850 -140 850 -110 {
lab=#net1}
N 790 -140 850 -140 {
lab=#net1}
N 790 -20 850 -20 {
lab=GND}
N 850 -50 850 -20 {
lab=GND}
N 620 -140 670 -140 {
lab=w3}
N 450 -140 500 -140 {
lab=w2}
N 290 -140 330 -140 {
lab=w1}
N 120 -140 170 -140 {
lab=w0}
N 120 -140 120 -80 {
lab=w0}
C {devices/code_shown.sym} -220 -540 0 0 {name=SPICE only_toplevel=false value=".lib /usr/local/share/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice tt
.include /usr/local/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice
.tran 0.01n 20n
.save all
vvcc vcc 0 dc 1.8
vvss vss 0 0
"}
C {devices/gnd.sym} 120 10 0 0 {name=l1 lab=GND}
C {sky130_stdcells/buf_1.sym} 210 -140 0 0 {name=x8 VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__ }
C {devices/capa.sym} 290 -80 0 0 {name=C1
m=1
value=0.1p
footprint=1206
device="ceramic capacitor"}
C {devices/gnd.sym} 290 10 0 0 {name=l3 lab=GND}
C {sky130_stdcells/buf_1.sym} 370 -140 0 0 {name=x9 VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__ }
C {devices/capa.sym} 450 -80 0 0 {name=C2
m=1
value=0.1p
footprint=1206
device="ceramic capacitor"}
C {devices/gnd.sym} 450 10 0 0 {name=l4 lab=GND}
C {sky130_stdcells/buf_1.sym} 540 -140 0 0 {name=x10 VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__ }
C {devices/capa.sym} 620 -80 0 0 {name=C3
m=1
value=0.1p
footprint=1206
device="ceramic capacitor"}
C {devices/gnd.sym} 620 10 0 0 {name=l5 lab=GND}
C {sky130_stdcells/buf_1.sym} 710 -140 0 0 {name=x11 VGND=VGND VNB=VNB VPB=VPB VPWR=VPWR prefix=sky130_fd_sc_hd__ }
C {devices/gnd.sym} 790 10 0 0 {name=l6 lab=GND}
C {devices/res.sym} 790 -80 0 0 {name=R2
value=100k
footprint=1206
device=resistor
m=1}
C {devices/capa.sym} 850 -80 0 0 {name=C4
m=1
value=0.002p
footprint=1206
device="ceramic capacitor"}
C {devices/lab_pin.sym} 290 -130 0 0 {name=l7 sig_type=std_logic lab=w1}
C {devices/lab_pin.sym} 450 -130 0 0 {name=l8 sig_type=std_logic lab=w2}
C {devices/lab_pin.sym} 620 -130 0 0 {name=l9 sig_type=std_logic lab=w3}
C {devices/vsource.sym} 120 -50 0 0 {name=V1 value="pulse(0 1.8 0.1ns 0.01ns 0.01ns 0.5ns 1ns)"}
C {devices/lab_pin.sym} 120 -130 0 0 {name=l2 sig_type=std_logic lab=w0}
