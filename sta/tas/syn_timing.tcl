avt_config simToolModel hspice
avt_config avtVddName "vdd"
avt_config avtVssName "vss"
avt_config tasBefig yes
avt_config tmaDriveCapaout yes
avt_config avtPowerCalculation yes
avt_config simSlope 20e-12

avt_config simPowerSupply 1.62
avt_config simTemperature 85

avt_LoadFile ../../../mpw4/thirdparty/open_pdk/C4M.Sky130/libs.tech/ngspice/C4M.Sky130_ss_model.spice spice
avt_LoadFile ../../../mpw4/thirdparty/open_pdk/C4M.Sky130/libs.ref/StdCellLib/spice/StdCellLib.spi spice

foreach cell {sff1_x4 sff1r_x4} {
    inf_SetFigureName $cell
    inf_MarkSignal sff_m "MASTER"
    inf_MarkSignal sff_s "FLIPFLOP+SLAVE"
}

avt_LoadFile ../arlet6502_syn.v verilog
set fig [hitas Arlet6502]

inf_SetFigureName Arlet6502
create_clock -period 10000 -waveform {5000 0} clk

set fig [ttv_LoadSpecifiedTimingFigure Arlet6502]
set stbfig [stb $fig]
stb_DisplaySlackReport [fopen slack.rep w] $stbfig * * ?? 10  all 10000
