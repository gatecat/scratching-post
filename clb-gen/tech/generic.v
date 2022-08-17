module clb_mux2(input a0, a1, s0, output x);
	assign x = s0 ? a1 : a0;
endmodule

module clb_mux4(input a0, a1, a2, a3, s0, s1, output x);
	assign x = s1 ? (s0 ? a3 : a2) : (s0 ? a1 : a0);
endmodule

module clb_buf(input a, output x);
	assign x = a;
endmodule

module clb_not(input a, output x);
	assign x = ~a;
endmodule

module clb_and(input a, b, output x);
	assign x = a & b;
endmodule

module clb_andnot(input a, b, output x);
	assign x = a & ~b;
endmodule

module clb_or(input a, b, output x);
	assign x = a | b;
endmodule

module clb_ornot(input a, b, output x);
	assign x = a | ~b;
endmodule

module clb_xor(input a, b, output x);
	assign x = a ^ b;
endmodule

module clb_nand(input a, b, output x);
	assign x = ~(a & b);
endmodule

module clb_nor(input a, b, output x);
	assign x = ~(a | b);
endmodule

module clb_xnor(input a, b, output x);
	assign x = ~(a ^ b);
endmodule

module clb_dff(input clk, d, output reg q);
	always @(posedge clk)
		q <= d;
endmodule

module clb_dffrs(input clk, d, rn, sn, output reg q);
	always @(posedge clk, negedge rn, negedge sn)
		if (!rn)
			q <= 0;
		else if (!sn)
			q <= 1;
		else
			q <= d;
endmodule
