start:
    li s0, 3
    li s1, 0xb1000000
    sw s0, 4(s1)
    li s0, 1
outerloop:
    li s1, 0xb1000000
    sw s0, 0(s1)
    jal ra, delay
    addi s0, s0, 1
    andi s2, s0, 0x0f
    addi s2, s2, 0x30
    li s1, 0xb2000000
    sw s2, 0(s1)
    j outerloop

delay:
    li t0, 36000
delayloop:
    addi t0, t0, -1
    bnez t0, delayloop
    jr ra
