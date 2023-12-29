module upcounter_top(
	input [37:0] io_in,
	output [37:0] io_out, io_oeb
);

wire clk = io_in[0];

gf180mcu_fd_ip_sram__sram512x8m8wm1 sram_i (
	.CLK(clk),
	.CEN(io_in[1]),
	.GWEN(io_in[2]),
	.WEN(8'b0),
	.A(io_in[11:3]),
	.D(io_in[19:12]),
	.Q(io_out[27:20])
);

assign io_out[19:0] = 1'b0;
assign io_out[37:29] = 1'b0;
assign io_oeb[19:0] = {20{1'b1}};
assign io_oeb[37:20] = {18{1'b0}};

// some dummy logic
reg [23:0] ctr;
always @(posedge clk)
	ctr <= ctr + 1'b1;
assign io_out[28] = ctr[23];

endmodule