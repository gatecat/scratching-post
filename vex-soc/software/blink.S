start:
    li s0, 3
    li s1, 0xb1000000
    sw s0, 4(s1)
    li s0, 1
outerloop:
    sw s0, 0(s1)
    jal ra, delay
    addi s0, s0, 1
    j outerloop

delay:
    li t0, 36000
delayloop:
    addi t0, t0, -1
    bnez t0, delayloop
    jr ra
