yosys -import

if {[info exists ::env(PDKROOT)]} {
	set PDKROOT $::env(PDKROOT)
} else {
	set PDKROOT "$::env(HOME)/skywater-pdk"
}

if {[info exists ::env(STDLIB)]} {
	set STDLIB $::env(STDLIB)
} else {
	set STDLIB "sky130_fd_sc_hd"
}

if {[info exists ::env(MEMROOT)]} {
	set MEMROOT $::env(MEMROOT)
} else {
	set MEMROOT "$::env(HOME)/sky130_sram_macros"
}

if {[info exists ::env(TOP)]} {
	set TOP $::env(TOP)
} else {
	set TOP "top"
}

set SCRIPTROOT [file dirname [file normalize [info script]]]

set LIBROOT "${PDKROOT}/libraries/${STDLIB}/latest/"
set STDLIBERTY "${LIBROOT}/timing/${STDLIB}__tt_025C_1v80.lib"

set MEMLIB_32X256 "${MEMROOT}/sky130_sram_1kbyte_1rw1r_32x256_8/sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib"
set MEMLIB_8X1024 "${MEMROOT}/sky130_sram_1kbyte_1rw1r_8x1024_8/sky130_sram_1kbyte_1rw1r_8x1024_8_TT_1p8V_25C.lib"

# Create a placeholdr constr file
set ABC_CONSTR [exec mktemp]
set f [open ${ABC_CONSTR} w]
puts $f "set_driving_cell ${STDLIB}__inv_1"
# TODO: determine a reasonable value here
puts $f "set_load 1.0"
close $f

read_liberty -lib ${STDLIBERTY}
read_liberty -lib ${MEMLIB_32X256}
read_liberty -lib ${MEMLIB_8X1024}

synth -flatten -top ${TOP} -run :fine
# TODO: memory mapping
memory_libmap -lib ${SCRIPTROOT}/mem_macros.txt
techmap -map ${SCRIPTROOT}/mem_map.v
synth -flatten -top ${TOP} -run fine:
dfflibmap -liberty ${STDLIBERTY}
opt
abc -script "+strash;ifraig;scorr;dc2;dretime;strash;&get,-n;&dch,-f;&nf,-D,10000;&put;buffer,-G,1000,-N,10;upsize,-D,10000;dnsize,-D,10000;stime,-p" -constr ${ABC_CONSTR} -liberty ${STDLIBERTY}
setundef -zero
clean -purge
stat -liberty ${STDLIBERTY} -liberty ${MEMLIB_32X256} -liberty ${MEMLIB_8X1024}

