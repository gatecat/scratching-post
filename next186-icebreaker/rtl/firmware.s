section .text  align=4
global _start              ; defined an entry point for the program
ORG 0 
foo:
	mov al, 0x55
	out 0, al

	mov cx,20
loop0:
	mov dx,65535
loop1:
	dec dx
	jnz loop1
	dec cx
 	jnz loop0


	mov al, 0xaa
	out 0, al

	mov cx,20
loop2:
	mov dx,65535
loop3:
	dec dx
	jnz loop3
	dec cx
 	jnz loop2

	jmp foo



section .data   align=4
dw 00
dw 00
