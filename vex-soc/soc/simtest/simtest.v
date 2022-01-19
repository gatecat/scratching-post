`timescale 1ns/1ps

module testbench;
	wire [37:0] io;
	top dut(.io(io));

	reg clk;
	always #20 clk = (clk === 1'b0);
	assign io[0] = clk;
	reg rstn = 1'b0;
	assign io[1] = rstn;

	spiflash flash_i (
		.clk(io[2]),
		.csb(io[3]),
		.io0(io[4]),
		.io1(io[5]),
		.io2(io[6]),
		.io3(io[7])
	);

	initial begin
		$dumpfile("testbench.vcd");
		$dumpvars(0, testbench);
		// Init
		repeat (10) @(posedge clk);
		rstn = 1'b1;
		repeat (10000) @(posedge clk);
		$finish;
	end

endmodule

`ifndef POSTSYN
// Bidirectional IO buffer
module BB(input T, I, output O, inout B);
	assign B = T ? 1'bz : I;
	assign O = B;
endmodule
`endif
