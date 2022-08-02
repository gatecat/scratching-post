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

set LIBROOT "${PDKROOT}/libraries/${STDLIB}/latest/"
set STDLIBERTY "${LIBROOT}/timing/${STDLIB}__tt_025C_1v80.lib"

# Create a placeholdr constr file
set ABC_CONSTR [exec mktemp]
set f [open ${ABC_CONSTR} w]
puts $f "set_driving_cell ${STDLIB}__inv_1"
# TODO: determine a reasonable value here
puts $f "set_load 1.0"
close $f

read_liberty -lib ${STDLIBERTY}
synth -flatten -top ${TOP} -run :fine
# TODO: memory mapping
synth -flatten -top ${TOP} -run fine:
dfflibmap -liberty ${STDLIBERTY}
opt
abc -script "+strash;ifraig;scorr;dc2;dretime;strash;&get,-n;&dch,-f;&nf,-D,10000;&put;buffer,-G,1000,-N,10;upsize,-D,10000;dnsize,-D,10000;stime,-p" -constr ${ABC_CONSTR} -liberty ${STDLIBERTY}
setundef -zero
clean -purge
stat -liberty ${STDLIBERTY}

