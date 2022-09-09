module fab_tb;
	wire [27:0] I_top;
	wire [27:0] T_top;
	reg [27:0] O_top = 0;
	wire [55:0] A_cfg, B_cfg;

	reg CLK;
	reg SelfWriteStrobe;
	reg [31:0] SelfWriteData;
	reg Rx = 1'b0;
	wire ComActive;
	wire ReceiveLED;
	reg s_clk = 1'b0;
	reg s_data = 1'b0;

	eFPGA_top top_i (
		.I_top(I_top),
		.T_top(T_top),
		.O_top(O_top),
		.A_config_C(A_cfg), .B_config_C(B_cfg),
		.CLK(CLK), .SelfWriteStrobe(SelfWriteStrobe), .SelfWriteData(SelfWriteData),
		.Rx(Rx),
		.ComActive(ComActive),
		.ReceiveLED(ReceiveLED),
		.s_clk(s_clk),
		.s_data(s_data)
	);
endmodule

module clk_buf(input A, output X);
assign X = A;
endmodule

