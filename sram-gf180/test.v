module upcounter_top(
	input [37:0] io_in,
	output [37:0] io_out, io_oeb
);

wire clk = io_in[0];

gf180mcu_fd_ip_sram__sram512x8m8wm1 sram_0 (
	.CLK(clk),
	.CEN(io_in[1]),
	.GWEN(~io_in[2]),
	.WEN(~{8{io_in[2]}}),
	.A(io_in[11:3]),
	.D(io_in[19:12]),
	.Q(io_out[27:20])
);

gf180mcu_fd_ip_sram__sram512x8m8wm1 sram_1 (
	.CLK(clk),
	.CEN(io_in[2]),
	.GWEN(~io_in[1]),
	.WEN(~{8{io_in[1]}}),
	.A(io_in[11:3]),
	.D(io_in[19:12]),
	.Q(io_out[35:28])
);


assign io_out[19:0] = 1'b0;
assign io_out[37] = 1'b0;
assign io_oeb[19:0] = {20{1'b1}};
assign io_oeb[37:20] = {18{1'b0}};

// some dummy logic
reg [23:0] ctr;
always @(posedge clk)
	ctr <= ctr + 1'b1;
assign io_out[36] = ctr[23];

endmodule