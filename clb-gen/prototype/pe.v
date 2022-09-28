module pe_test(input [31:0] i0, i1, i2, input [1:0] op, output [31:0] o);
	wire [31:0] tmp = op[0] ? (i0 * i1) : i0;
	assign o = op[1] ? (tmp + i2) : tmp;
endmodule
