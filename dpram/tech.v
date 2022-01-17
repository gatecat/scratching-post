`timescale 1ps/1ps

// Some test cells with made-up delays (in ps)
module INV(input A, output Q);
	assign #200 Q = ~A;
endmodule

module BUF(input A, output Q);
	assign #400 Q = A;
endmodule

module XOR(input A, B, output Q);
	assign #600 Q = A^B;
endmodule

module OR(input A, B, output Q);
	assign #600 Q = A|B;
endmodule

module AND(input A, B, output Q);
	assign #600 Q = A&B;
endmodule

module NAND(input A, B, output Q);
	assign #400 Q = ~(A&B);
endmodule

module MUX2(input A, B, S, output Q);
	assign #600 Q = S?B:A;
endmodule



// Example of a 256x8 RAM macro
// Note that this assumes the read latches keep their old value in a write
// if that isn't the case; an extra RAM macro will be needed
module RAM_BLOCK(input CLK, input [7:0] ADDR, WDATA, input RD_WRN, output reg [7:0] RDATA);
	reg [7:0] mem[0:255];
	always @(posedge CLK)
		if (RD_WRN)
			RDATA <= #1000 mem[ADDR];
		else
			mem[ADDR] <= WDATA;
endmodule


