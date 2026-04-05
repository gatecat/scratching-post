module testbench;

	reg clk;
	always #5 clk = (clk === 1'b0);

	localparam ser_half_period = 53;
	event ser_sample;

	initial begin
		$dumpfile("testbench.vcd");
		$dumpvars(0, testbench);

		repeat (10000) @(posedge clk);

		$finish;
	end

	wire ledr, ledg;

	top dut_i (
	    .CLK(clk),

	    .TX(),
	    .RX(1'b0),

	    .BTN_N(1'b1),
	    .LEDR_N(ledr),
	    .LEDG_N(ledg)
	);



endmodule
