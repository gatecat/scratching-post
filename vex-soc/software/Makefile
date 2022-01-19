all: blink.bin

blink.elf: sections.lds blink.S
	riscv64-linux-gnu-gcc -march=rv32ima -mabi=ilp32 -Wl,--build-id=none,-Bstatic,-T,sections.lds,--strip-debug -static -ffreestanding -nostdlib -o blink.elf blink.S

blink.bin: blink.elf
	riscv64-linux-gnu-objcopy -O binary blink.elf blink.bin

blink.prog: blink.bin
	ecpprog -k 2 -o 1M blink.bin

.PHONY: blink.prog

