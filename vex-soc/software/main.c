#include <stdint.h>
#include "riscv.h"

#include "drivers/uart.h"
#include "drivers/soc_id.h"

volatile uart_regs_t *const UART0 = (volatile uart_regs_t*)0xb2000000;
volatile soc_id_regs_t *const SOC_ID = (volatile soc_id_regs_t*)0xb4000000;

volatile uint32_t *const LED = (volatile uint32_t *)0xb1000000;

volatile uint32_t *const UART_TX = (volatile uint32_t *)0xb2000000;
volatile uint32_t *const UART_RX = (volatile uint32_t *)0xb2000004;
volatile uint32_t *const UART_TX_RDY = (volatile uint32_t *)0xb2000008;
volatile uint32_t *const UART_RX_AVL = (volatile uint32_t *)0xb200000c;

volatile uint32_t *const TIME_LOW = (volatile uint32_t *)0xb3000000;
volatile uint32_t *const TIME_HIGH = (volatile uint32_t *)0xb3000004;

volatile uint32_t *const SPICTRL = (volatile uint32_t *)0xb0000000;


#define max(a,b) \
	({ __typeof__ (a) _a = (a); \
	 __typeof__ (b) _b = (b); \
	 _a > _b ? _a : _b; })


#define min(a,b) \
	({ __typeof__ (a) _a = (a); \
	 __typeof__ (b) _b = (b); \
	 _a < _b ? _a : _b; })


void putc(char c) {
	if (c == '\n') putc('\r');
	while (!(*UART_TX_RDY & 0x1)) {
	}
	*UART_TX = c;
}

void puts(const char *s) {
	while (*s != 0)
		putc(*s++);
}

void puthex(uint32_t x) {
	for (int i = 7; i >= 0; i--) {
		uint8_t nib = (x >> (4 * i)) & 0xF;
		if (nib <= 9)
			putc('0' + nib);
		else
			putc('A' + (nib - 10));
	}
}

void delay() {
	for (volatile int i = 0; i < 25000; i++)
		;
}

extern uint32_t flashio_worker_begin;
extern uint32_t flashio_worker_end;

void flashio(uint8_t *data, int len, uint8_t wrencmd)
{
	volatile uint32_t func[&flashio_worker_end - &flashio_worker_begin];

	uint32_t *src_ptr = &flashio_worker_begin;
	volatile uint32_t *dst_ptr = func;

	while (src_ptr != &flashio_worker_end)
		*(dst_ptr++) = *(src_ptr++);

	__asm__ volatile ("fence.i" : : : "memory");

	((void(*)(uint8_t*, uint32_t, uint32_t))func)(data, len, wrencmd);
}


void cmd_read_flash_id()
{
	uint8_t buffer[5] = { 0x9F, /* zeros */ };
	flashio(buffer, 5, 0);

	uint32_t id = 0;
	for (int i = 1; i <= 4; i++) {
		id = id << 8U;
		id |= buffer[i];
	}
	puts("Flash ID: ");
	puthex(id);
	puts("\n");
}

void set_flash_qspi_flag()
{
	uint8_t buffer[8];

	// Read Configuration Registers (RDCR1 35h)
	buffer[0] = 0x35;
	buffer[1] = 0x00; // rdata
	flashio(buffer, 2, 0);
	uint8_t sr2 = buffer[1];

	// Write Enable Volatile (50h) + Write Status Register 2 (31h)
	buffer[0] = 0x31;
	buffer[1] = sr2 | 2; // Enable QSPI
	flashio(buffer, 2, 0x50);
}

void set_flash_mode_quad()
{
	*SPICTRL = (*SPICTRL & ~0x007f0000) | 0x00240000;
}

void set_flash_mode_qddr()
{
	*SPICTRL = (*SPICTRL & ~0x007f0000) | 0x00670000;
}

void enable_flash_crm()
{
	*SPICTRL |= 0x00100000;
}

#define __stacktop ((uint32_t*)0x10FFFF00)

__attribute__((naked)) static void vexriscv_machine_mode_trap_entry(void) {
	__asm__ __volatile__ (
	"csrrw sp, mscratch, sp\n"
	"sw x1,   1*4(sp)\n"
	"sw x3,   3*4(sp)\n"
	"sw x4,   4*4(sp)\n"
	"sw x5,   5*4(sp)\n"
	"sw x6,   6*4(sp)\n"
	"sw x7,   7*4(sp)\n"
	"sw x8,   8*4(sp)\n"
	"sw x9,   9*4(sp)\n"
	"sw x10,   10*4(sp)\n"
	"sw x11,   11*4(sp)\n"
	"sw x12,   12*4(sp)\n"
	"sw x13,   13*4(sp)\n"
	"sw x14,   14*4(sp)\n"
	"sw x15,   15*4(sp)\n"
	"sw x16,   16*4(sp)\n"
	"sw x17,   17*4(sp)\n"
	"sw x18,   18*4(sp)\n"
	"sw x19,   19*4(sp)\n"
	"sw x20,   20*4(sp)\n"
	"sw x21,   21*4(sp)\n"
	"sw x22,   22*4(sp)\n"
	"sw x23,   23*4(sp)\n"
	"sw x24,   24*4(sp)\n"
	"sw x25,   25*4(sp)\n"
	"sw x26,   26*4(sp)\n"
	"sw x27,   27*4(sp)\n"
	"sw x28,   28*4(sp)\n"
	"sw x29,   29*4(sp)\n"
	"sw x30,   30*4(sp)\n"
	"sw x31,   31*4(sp)\n"
	"call vexriscv_machine_mode_trap\n"
	"lw x1,   1*4(sp)\n"
	"lw x3,   3*4(sp)\n"
	"lw x4,   4*4(sp)\n"
	"lw x5,   5*4(sp)\n"
	"lw x6,   6*4(sp)\n"
	"lw x7,   7*4(sp)\n"
	"lw x8,   8*4(sp)\n"
	"lw x9,   9*4(sp)\n"
	"lw x10,   10*4(sp)\n"
	"lw x11,   11*4(sp)\n"
	"lw x12,   12*4(sp)\n"
	"lw x13,   13*4(sp)\n"
	"lw x14,   14*4(sp)\n"
	"lw x15,   15*4(sp)\n"
	"lw x16,   16*4(sp)\n"
	"lw x17,   17*4(sp)\n"
	"lw x18,   18*4(sp)\n"
	"lw x19,   19*4(sp)\n"
	"lw x20,   20*4(sp)\n"
	"lw x21,   21*4(sp)\n"
	"lw x22,   22*4(sp)\n"
	"lw x23,   23*4(sp)\n"
	"lw x24,   24*4(sp)\n"
	"lw x25,   25*4(sp)\n"
	"lw x26,   26*4(sp)\n"
	"lw x27,   27*4(sp)\n"
	"lw x28,   28*4(sp)\n"
	"lw x29,   29*4(sp)\n"
	"lw x30,   30*4(sp)\n"
	"lw x31,   31*4(sp)\n"
	"csrrw sp, mscratch, sp\n"
	"mret\n"
	);
}

static int vexriscv_read_register(uint32_t id){
	unsigned int sp = (unsigned int) (__stacktop);
	return ((int*) sp)[id-32];
}
static void vexriscv_write_register(uint32_t id, int value){
	uint32_t sp = (uint32_t) (__stacktop);
	((uint32_t*) sp)[id-32] = value;
}



void print_trap(void) {
	puts("😿: mraow~!\n");

	puts("      mcause: ");
	puthex(csr_read(mcause));
	puts("\n");

	puts("      mepc: ");
	puthex(csr_read(mepc));
	puts("\n");

	puts("      mstatus: ");
	puthex(csr_read(mstatus));
	puts("\n");

	puts("      mbadaddr: ");
	puthex(csr_read(mbadaddr));
	puts("\n");

	puts("      regs:\n");
	puthex(0);
	puts(" ");
	for (int i = 1; i < 32; i++) {
		puthex(vexriscv_read_register(i));
		if ((i % 4) == 3)
			puts("\n");
		else
			puts(" ");
	}
	puts("\n");
}

void default_trap(void) {
	print_trap();
	while(1) {};
}


#define vexriscv_trap_barrier_start \
		"  	li       %[tmp],  0x00020000\n" \
		"	csrs     mstatus,  %[tmp]\n" \
		"  	la       %[tmp],  1f\n" \
		"	csrw     mtvec,  %[tmp]\n" \
		"	li       %[fail], 1\n" \

#define vexriscv_trap_barrier_end \
		"	li       %[fail], 0\n" \
		"1:\n" \
		"  	li       %[tmp],  0x00020000\n" \
		"	csrc     mstatus,  %[tmp]\n" \

static int32_t vexriscv_read_word(uint32_t address, int32_t *data){
	int32_t result, tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	lw       %[result], 0(%[address])\n"
		vexriscv_trap_barrier_end
		: [result]"=&r" (result), [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address)
		: "memory"
	);

	*data = result;
	return fail;
}

static int32_t vexriscv_read_word_unaligned(uint32_t address, int32_t *data){
	int32_t result, tmp;
	int32_t fail;
	__asm__ __volatile__ (
			vexriscv_trap_barrier_start
		"	lbu      %[result], 0(%[address])\n"
		"	lbu      %[tmp],    1(%[address])\n"
		"	slli     %[tmp],  %[tmp], 8\n"
		"	or       %[result], %[result], %[tmp]\n"
		"	lbu      %[tmp],    2(%[address])\n"
		"	slli     %[tmp],  %[tmp], 16\n"
		"	or       %[result], %[result], %[tmp]\n"
		"	lbu      %[tmp],    3(%[address])\n"
		"	slli     %[tmp],  %[tmp], 24\n"
		"	or       %[result], %[result], %[tmp]\n"
		vexriscv_trap_barrier_end
		: [result]"=&r" (result), [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address)
		: "memory"
	);

	*data = result;
	return fail;
}

static int32_t vexriscv_read_half_unaligned(uint32_t address, int32_t *data){
	int32_t result, tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	lb       %[result], 1(%[address])\n"
		"	slli     %[result],  %[result], 8\n"
		"	lbu      %[tmp],    0(%[address])\n"
		"	or       %[result], %[result], %[tmp]\n"
		vexriscv_trap_barrier_end
		: [result]"=&r" (result), [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address)
		: "memory"
	);

	*data = result;
	return fail;
}

static int32_t vexriscv_write_word(uint32_t address, int32_t data){
	int32_t tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	sw       %[data], 0(%[address])\n"
		vexriscv_trap_barrier_end
		: [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address), [data]"r" (data)
		: "memory"
	);

	return fail;
}


static int32_t vexriscv_write_word_unaligned(uint32_t address, int32_t data){
	int32_t tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	sb       %[data], 0(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 1(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 2(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 3(%[address])\n"
		vexriscv_trap_barrier_end
		: [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address), [data]"r" (data)
		: "memory"
	);

	return fail;
}



static int32_t vexriscv_write_short_unaligned(uint32_t address, int32_t data){
	int32_t tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	sb       %[data], 0(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 1(%[address])\n"
		vexriscv_trap_barrier_end
		: [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address), [data]"r" (data)
		: "memory"
	);

	return fail;
}

static void vexriscv_machine_mode_trap_to_supervisor_trap(uint32_t sepc, uint32_t mstatus){
	csr_write(mtvec,    vexriscv_machine_mode_trap_entry);
	csr_write(sbadaddr, csr_read(mbadaddr));
	csr_write(scause,   csr_read(mcause));
	csr_write(sepc,     sepc);
	csr_write(mepc,	    csr_read(stvec));
	csr_write(mstatus,
			  (mstatus & ~(MSTATUS_SPP | MSTATUS_MPP | MSTATUS_SIE | MSTATUS_SPIE))
			| ((mstatus >> 3) & MSTATUS_SPP)
			| (0x0800 | MSTATUS_MPIE)
			| ((mstatus & MSTATUS_SIE) << 4)
	);
}


static uint32_t vexriscv_read_instruction(uint32_t pc){
	uint32_t i;
	if (pc & 2) {
		vexriscv_read_word(pc - 2, (int32_t*)&i);
		i >>= 16;
		if ((i & 3) == 3) {
			uint32_t u32Buf;
			vexriscv_read_word(pc+2, (int32_t*)&u32Buf);
			i |= u32Buf << 16;
		}
	} else {
		vexriscv_read_word(pc, (int32_t*)&i);
	}
	return i;
}

static uint32_t vexriscv_sbi_ext(uint32_t fid, uint32_t extid){
	switch (fid) {
		case SBI_EXT_SPEC_VERSION:
			return 0x00000001;
		case SBI_EXT_IMPL_ID:
			return 0;
		case SBI_EXT_IMPL_VERSION:
			return 0;
		case SBI_EXT_PROBE_EXTENSION:
			break;
		case SBI_EXT_GET_MVENDORID:
			return 0;
		case SBI_EXT_GET_MARCHID:
			return 0;
		case SBI_EXT_GET_MIMPID:
			return 0;
		default:
			return 0;
	}

	/* sbi_probe_extension() */
	switch (extid) {
		case SBI_CONSOLE_PUTCHAR:
		case SBI_CONSOLE_GETCHAR:
		case SBI_SET_TIMER:
		case SBI_EXT_BASE:
			return 1;
		default:
			return 0;
	}
}

__attribute__((used)) void vexriscv_machine_mode_trap(void) {

	int32_t cause = csr_read(mcause);

	// print_trap();

	/* Interrupt */
	if(cause < 0){
		switch(cause & 0xff){
			case CAUSE_MACHINE_TIMER: {
				csr_set(sip, MIP_STIP);
				csr_clear(mie, MIE_MTIE);
			} break;
			default: default_trap(); break;
		}
	/* Exception */
	} else {
		switch(cause){
		    case CAUSE_UNALIGNED_LOAD:{
			    uint32_t mepc = csr_read(mepc);
			    uint32_t mstatus = csr_read(mstatus);
			    uint32_t instruction = vexriscv_read_instruction(mepc);
			    uint32_t address = csr_read(mbadaddr);
			    uint32_t func3 =(instruction >> 12) & 0x7;
			    uint32_t rd = (instruction >> 7) & 0x1F;
			    int32_t readValue;
			    int32_t fail = 1;

			    switch(func3){
			    case 1: fail = vexriscv_read_half_unaligned(address, &readValue); break;  //LH
			    case 2: fail = vexriscv_read_word_unaligned(address, &readValue); break; //LW
			    case 5: fail = vexriscv_read_half_unaligned(address, &readValue) & 0xFFFF; break; //LHU
			    }

			    if(fail){
			    	puts("failed!!\n");
				    vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
				    return;
			    }
			    vexriscv_write_register(rd, readValue);
			    csr_write(mepc, mepc + 4);
			    csr_write(mtvec, vexriscv_machine_mode_trap_entry); //Restore mtvec
		    }break;
		    case CAUSE_UNALIGNED_STORE:{
			    uint32_t mepc = csr_read(mepc);
			    uint32_t mstatus = csr_read(mstatus);
			    uint32_t instruction = vexriscv_read_instruction(mepc);
			    uint32_t address = csr_read(mbadaddr);
			    uint32_t func3 =(instruction >> 12) & 0x7;
			    int32_t writeValue = vexriscv_read_register((instruction >> 20) & 0x1F);
			    int32_t fail = 1;

			    switch(func3){
			    case 1: fail = vexriscv_write_short_unaligned(address, writeValue); break; //SH
			    case 2: fail = vexriscv_write_word_unaligned(address, writeValue); break; //SW
			    }

			    if(fail){
				    vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
				    return;
			    }

			    csr_write(mepc, mepc + 4);
			    csr_write(mtvec, vexriscv_machine_mode_trap_entry); //Restore mtvec
		    }break;
			/* Illegal instruction */
			case CAUSE_ILLEGAL_INSTRUCTION:{
				uint32_t mepc = csr_read(mepc);
				uint32_t mstatus = csr_read(mstatus);
				uint32_t instr = csr_read(mbadaddr);

				uint32_t opcode = instr & 0x7f;
				uint32_t funct3 = (instr >> 12) & 0x7;
				switch(opcode){
					/* Atomic */
					case 0x2f:
						switch(funct3){
							case 0x2:{
								uint32_t sel = instr >> 27;
								uint32_t addr = vexriscv_read_register((instr >> 15) & 0x1f);
								int32_t src = vexriscv_read_register((instr >> 20) & 0x1f);
								uint32_t rd = (instr >> 7) & 0x1f;
								int32_t read_value;
								int32_t write_value = 0
								;
								if(vexriscv_read_word(addr, &read_value)) {
									vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
									return;
								}

								switch(sel){
									case 0x0:  write_value = src + read_value; break;
									case 0x1:  write_value = src; break;
									case 0x2:  break; /*  LR, SC done in hardware (cheap) and require */
									case 0x3:  break; /*  to keep track of context switches */
									case 0x4:  write_value = src ^ read_value; break;
									case 0xC:  write_value = src & read_value; break;
									case 0x8:  write_value = src | read_value; break;
									case 0x10: write_value = min(src, read_value); break;
									case 0x14: write_value = max(src, read_value); break;
									case 0x18: write_value = min((unsigned int)src, (unsigned int)read_value); break;
									case 0x1C: write_value = max((unsigned int)src, (unsigned int)read_value); break;
									default: default_trap(); return; break;
								}
								if(vexriscv_write_word(addr, write_value)){
									vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
									return;
								}
								vexriscv_write_register(rd, read_value);
								csr_write(mepc, mepc + 4);
								csr_write(mtvec, vexriscv_machine_mode_trap_entry); /* Restore MTVEC */
							} break;
							default: default_trap(); break;
						} break;
					/* CSR */
					case 0x73:{
						uint32_t input = (instr & 0x4000) ? ((instr >> 15) & 0x1f) : vexriscv_read_register((instr >> 15) & 0x1f);
						__attribute__((unused)) uint32_t clear, set;
						uint32_t write;
						switch (funct3 & 0x3) {
							case 0: default_trap(); break;
							case 1: clear = ~0; set = input; write = 1; break;
							case 2: clear = 0; set = input; write = ((instr >> 15) & 0x1f) != 0; break;
							case 3: clear = input; set = 0; write = ((instr >> 15) & 0x1f) != 0; break;
						}
						uint32_t csrAddress = instr >> 20;
						uint32_t old;
						switch(csrAddress){
							case RDCYCLE :
							case RDINSTRET:
							case RDTIME  : old = *TIME_LOW; break;
							case RDCYCLEH :
							case RDINSTRETH:
							case RDTIMEH : old = *TIME_HIGH; break;
							default: default_trap(); break;
						}
						if(write) {
							switch(csrAddress){
								default: default_trap(); break;
							}
						}

						vexriscv_write_register((instr >> 7) & 0x1f, old);
						csr_write(mepc, mepc + 4);

					} break;
					default: default_trap(); break;
				}
			} break;
			case CAUSE_SCALL:{
				uint32_t which = vexriscv_read_register(17);
				uint32_t a0 = vexriscv_read_register(10);
				uint32_t a1 = vexriscv_read_register(11);
				__attribute__((unused)) uint32_t a2 = vexriscv_read_register(12);
				switch(which){
					case SBI_CONSOLE_PUTCHAR: {
						putc(a0);
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
					case SBI_CONSOLE_GETCHAR: {
						vexriscv_write_register(10, 0);
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
					case SBI_SET_TIMER: {
						*TIME_HIGH = a1;
						*TIME_LOW = a0;
						csr_set(mie, MIE_MTIE);
						csr_clear(sip, MIP_STIP);
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
					case SBI_EXT_BASE: {
						vexriscv_write_register(10, vexriscv_sbi_ext(a0, a1));
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
					default: {
						vexriscv_write_register(10, -2); /* SBI_ERR_NOT_SUPPORTED */
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
				}
			} break;
			default: default_trap(); break;
		}
	}
}

void main() {
	uart_puts(UART0, "🐱: nyaa~!\n");

	uart_puts(UART0, "SoC type: ");
	uart_puthex(UART0, SOC_ID->type);
	uart_puts(UART0, "\n");

	uart_puts(UART0, "SoC version: ");
	uart_puthex(UART0, SOC_ID->version);
	uart_puts(UART0, "\n");

	cmd_read_flash_id();

	uart_puts(UART0, "Setting QSPI flag\n");
	set_flash_qspi_flag();
	uart_puts(UART0, "Entering quad mode\n");
	set_flash_mode_quad();
	uart_puts(UART0, "Flash configuration done!\n");


	csr_write(mtvec,    vexriscv_machine_mode_trap_entry);
	csr_write(mscratch, ((uint32_t)__stacktop )- 32 * 4); // exception stack pointer
	csr_write(mstatus,  0x0800 | MSTATUS_MPIE);
	csr_write(mie,      0);
	csr_write(mepc, 0x00800000); // Linux image base
	csr_write(medeleg, MEDELEG_INSTRUCTION_PAGE_FAULT | MEDELEG_LOAD_PAGE_FAULT | MEDELEG_STORE_PAGE_FAULT | MEDELEG_USER_ENVIRONNEMENT_CALL);
	csr_write(mideleg, MIDELEG_SUPERVISOR_TIMER | MIDELEG_SUPERVISOR_EXTERNAL | MIDELEG_SUPERVISOR_SOFTWARE);
	puts("about to boop the kernel, ganbatte~!\n");
	__asm__ __volatile__ (
		// zero initial memory
		" li t0, 0x10000000\n"
		" li t1, 0x10100000\n"
		"1:\n"
		" sw x0, 0(t0)\n"
		" addi t0, t0, 4\n"
		" blt t0, t1, 1b\n"
		// boot kernel
		" li a0, 0\n"
		" li a1, %0\n"
		" mret"
		 : : "i" (0x00f80000) // DTB base
	);
}
