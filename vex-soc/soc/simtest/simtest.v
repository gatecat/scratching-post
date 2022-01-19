`timescale 1ns/1ps

module testbench;
	wire [37:0] io;
	top dut(.io(io));

	reg clk;
	always #20 clk = (clk === 1'b0);
	assign io[0] = clk;
	reg rstn = 1'b0;
	assign io[1] = rstn;

	assign io[31] = 1'b1; // uart tx
	wire uart_tx = io[30];

	wire [1:0] gpio = io[37:36];

	spiflash flash_i (
		.clk(io[2]),
		.csb(io[3]),
		.io0(io[4]),
		.io1(io[5]),
		.io2(io[6]),
		.io3(io[7])
	);


	s27kl0642 ram0_i(
		.DQ7(io[18]), .DQ6(io[17]), .DQ5(io[16]), .DQ4(io[15]), .DQ3(io[14]), .DQ2(io[13]), .DQ1(io[12]), .DQ0(io[11]),
		.RWDS(io[10]),
		.CSNeg(io[9]),
		.CK(io[8]), .CKn(~io[8]),
		.RESETNeg(rstn)
	);

	s27kl0642 ram1_i(
		.DQ7(io[29]), .DQ6(io[28]), .DQ5(io[27]), .DQ4(io[26]), .DQ3(io[25]), .DQ2(io[24]), .DQ1(io[23]), .DQ0(io[22]),
		.RWDS(io[21]),
		.CSNeg(io[20]),
		.CK(io[19]), .CKn(~io[19]),
		.RESETNeg(rstn)
	);

	initial begin
		$dumpfile("testbench.vcd");
		$dumpvars(0, testbench);
		// Init
		repeat (10) @(posedge clk);
		rstn = 1'b1;
		repeat (100000) @(posedge clk);
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
