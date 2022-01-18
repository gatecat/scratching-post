VEX_DIR=../../pythondata-cpu-vexriscv/pythondata_cpu_vexriscv/verilog

generate: VexRiscv_LinuxMpw.v

VexRiscv_LinuxMpw.v:
	( cd ${VEX_DIR} && sbt compile "runMain vexriscv.GenCoreDefault --csrPluginConfig linux-minimal --iCacheSize 512 --dCacheSize 256  --singleCycleMulDiv=false --relaxedPcCalculation=true --prediction=none --outputFile VexRiscv_LinuxMpw" )
	cp ${VEX_DIR}/$@ .

.PHONY: generate
.SECONDARY: VexRiscv_LinuxMpw.v
