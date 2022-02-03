all: blink.bin

blink.elf: sections.lds blink.S
	riscv64-linux-gnu-gcc -march=rv32ima -mabi=ilp32 -Wl,--build-id=none,-Bstatic,-T,sections.lds,--strip-debug -static -ffreestanding -nostdlib -o blink.elf blink.S

blink.bin: blink.elf
	riscv64-linux-gnu-objcopy -O binary blink.elf blink.bin

blink.prog: blink.bin
	ecpprog -k 2 -o 1M blink.bin

bios.elf: sections.lds start.s main.c $(wildcard drivers/*.c)
	riscv32-unknown-linux-gnu-gcc -g -march=rv32ima -mabi=ilp32 -Wl,--build-id=none,-Bstatic,-T,sections.lds,--strip-debug -static -ffreestanding -nostdlib -o bios.elf start.s main.c $(wildcard drivers/*.c)

bios.bin: bios.elf
	riscv64-linux-gnu-objcopy -O binary bios.elf bios.bin

bios.prog: bios.bin
	ecpprog -k 2 -o 1M bios.bin


.PHONY: blink.prog bios.prog

