start:
	li a0, 0xf0
	jal uart_putc
	li a0, 0x9f
	jal uart_putc
	li a0, 0x90
	jal uart_putc
	li a0, 0xb1
	jal uart_putc
	li a0, 0x0d
	jal uart_putc
	li a0, 0x0a
	jal uart_putc
	# Write test pattern
	li t0, 0x10f00000
	li t1, 0xFF00FF00
	li t2, 0x00FF00FF
	sw t1, 0(t0)
	sw t2, 4(t0)
	sw t1, 8(t0)
	sw t2, 12(t0)
	sw t1, 16(t0)
	sw t2, 20(t0)

	jal flush_dcache

	lw a0, 0(t0)
	jal uart_putbin
	lw a0, 4(t0)
	jal uart_putbin
	lw a0, 8(t0)
	jal uart_putbin
	lw a0, 12(t0)
	jal uart_putbin
	lw a0, 16(t0)
	jal uart_putbin
	lw a0, 20(t0)
	jal uart_putbin

done:
	j done

flush_dcache:
	# Just read 4kB of flash to avoid disrupting trace
	li t0, 4092
1:
	lw t1, 0(t0)
	addi t0, t0, -4
	bnez t0, 1b
	jr ra

uart_putbin:
	li t1, 32
	mv s0, a0
	mv s1, ra
1:
	srli t2, s0, 31
	slli s0, s0, 1
	addi a0, t2, 0x30 
	jal uart_putc
	addi t1, t1, -1
	bnez t1, 1b

	# CRLF
	li a0, 0x0d
	jal uart_putc
	li a0, 0x0a
	jal uart_putc

	jr s1

uart_putc:
	# Wait for ready
	li t0, 0xb2000000
	lw t0, 8(t0)
	beqz t0, uart_putc
	# Output char
	li t0, 0xb2000000
	sw a0, 0(t0)
	jr ra
