module sky130_fd_sc_hd__dlxtn_1(input D, GATE_N, output reg Q);
	always @(*) if (~GATE_N) Q <= D;
endmodule

module sky130_fd_sc_hd__mux4_1(input A0, A1, A2, A3, input S0, S1, output X);
	assign X = S1 ? (S0 ? A3 : A2) : (S0 ? A1 : A0);
endmodule

module sky130_fd_sc_hd__nand2_1(input A, B, output Y);
	assign Y = ~(A & B);
endmodule

module sky130_fd_sc_hd__inv_1(input A, output Y);
	assign Y = ~A;
endmodule

module sky130_fd_sc_hd__xnor2_1(input A, B, output Y);
	assign Y = ~(A ^ B);
endmodule

module sky130_fd_sc_hd__mux2i_1(input A0, A1, S, output Y);
	assign Y = ~(S ? A1 : A0);
endmodule

module sky130_fd_sc_hd__dfsbp_1(input D, SET_B, CLK, output reg Q, output Q_N);
	always @(posedge CLK, negedge SET_B)
		if (~SET_B)
			Q <= 1'b1;
		else
			Q <= D;
	assign Q_N = ~Q;
endmodule

module sky130_fd_sc_hd__buf_4(input A, output X);
	assign X = A;
endmodule

module sky130_fd_sc_hd__clkbuf_4(input A, output X);
	assign X = A;
endmodule