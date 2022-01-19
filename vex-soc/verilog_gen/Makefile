SRC := ${shell find . -type f -name \*.scala}

all: VexRiscvLinuxAsic.v

VexRiscvLinuxAsic.v: $(SRC)
	sbt compile "runMain vexriscv.GenCoreDefault"
