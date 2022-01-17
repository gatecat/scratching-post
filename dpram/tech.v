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
