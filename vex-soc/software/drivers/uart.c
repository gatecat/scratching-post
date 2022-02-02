#include "uart.h"

void uart_putc(volatile uart_regs_t *uart, char c) {
	if (c == '\n')
		uart_putc(uart, '\r');
	while (!uart->tx_ready)
		;
	uart->tx_data = c;
}

void uart_puts(volatile uart_regs_t *uart, const char *s) {
	while (*s != 0)
		uart_putc(uart, *s++);
}

