#include <stdint.h>

volatile uint8_t *const LED = (volatile uint8_t *)0xb1000000;


volatile uint8_t *const UART_TX = (volatile uint8_t *)0xb2000000;
volatile uint8_t *const UART_RX = (volatile uint8_t *)0xb2000004;
volatile uint8_t *const UART_TX_RDY = (volatile uint8_t *)0xb2000008;
volatile uint8_t *const UART_RX_AVL = (volatile uint8_t *)0xb200000c;

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

void main() {
	puts("🐱: nyaa~!\n");
	while(1) {
		*LED = 2;
		*LED = 1;
	};
}
