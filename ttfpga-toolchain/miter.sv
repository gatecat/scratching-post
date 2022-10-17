module miter(
	input fab_clk,
	input [3:0] io_in,
	output [119:0] cfg,
	output [7:0] fab_io_out,
	output [7:0] gold_io_out
);
	assign cfg = $anyconst;
	fabric fab_i (
  		.fab_clk(fab_clk),
    	.cfg(cfg),
   		.io_in(io_in), 
  		.io_out(fab_io_out)
	);

	user_design gold_i(
		.fab_clk(fab_clk),
		.io_in(io_in),
		.io_out(gold_io_out)
	);

	always @* assert(fab_io_out == gold_io_out);
endmodule
