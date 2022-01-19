start:
    li s0, 3
    li s1, 0xb1000000
    sw s0, 4(s1)
outerloop:
    li s0, 1
    sw s0, 0(s1)
    jal ra, delay
    li s0, 2
    sw s0, 0(s1)
    jal ra, delay
    j outerloop

delay:
    li t0, 3600000
delayloop:
    addi t0, t0, -1
    bnez t0, delayloop
    jr ra
