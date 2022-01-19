#include <stdint.h>

volatile uint32_t *const LED = (volatile uint32_t *)0xb1000000;


volatile uint32_t *const UART_TX = (volatile uint32_t *)0xb2000000;
volatile uint32_t *const UART_RX = (volatile uint32_t *)0xb2000004;
volatile uint32_t *const UART_TX_RDY = (volatile uint32_t *)0xb2000008;
volatile uint32_t *const UART_RX_AVL = (volatile uint32_t *)0xb200000c;

void putc(char c) {
	if (c == '\n') putc('\r');
	while (!(*UART_TX_RDY & 0x1)) {
		*LED = 0;
	}
	*LED = 3;
	*UART_TX = c;
}

void puts(const char *s) {
	while (*s != 0)
		putc(*s++);
}

void delay() {
	for (volatile int i = 0; i < 25000; i++)
		;
}

#define csr_write(csr, val)					\
({								\
	unsigned long __v = (unsigned long)(val);		\
	__asm__ __volatile__ ("csrw " #csr ", %0"		\
						      : : "rK" (__v));			\
})

void main() {
	puts("🐱: nyaa~!\n");
	csr_write(mepc, 0x00200000); // Linux image base
	__asm__ __volatile__ (
		" li a0, 0\n"
		" li a1, %0\n"
		" mret"
		 : : "i" (0x00180000) // DTB base
	);
}
