module user_design(
	input fab_clk,
	input [3:0] io_in,
	output [7:0] io_out,
);

assign io_out = {4'b0, io_in};

endmodule
