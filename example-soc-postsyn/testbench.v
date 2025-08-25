`timescale 1 ns / 1 ps

module testbench;

	reg clk = 1;
	reg resetn = 0;

	always #5 clk = ~clk;

	initial begin

		$dumpfile("testbench.fst");
		$dumpvars(0, testbench);

		repeat (100) @(posedge clk);
		resetn <= 1;
		repeat (1000000) @(posedge clk);
		$finish;
	end

	wire [43:0] gpio_in, gpio_oeb, gpio_out;

	openframe_project_wrapper dut_i (
		.gpio_in(gpio_in),
		.gpio_out(gpio_out),
		.gpio_oeb(gpio_oeb)
	);

	assign gpio_in[38] = clk;
	assign gpio_in[40] = resetn;

	wire soc_flash_clk = gpio_out[0];
	wire soc_flash_csn = gpio_out[1];
	wire [3:0] soc_flash_out = gpio_out[5:2];
	wire [3:0] soc_flash_oeb = gpio_oeb[5:2];


	// simulate flash tristate IO buffers
	wire [3:0] soc_flash_d;
	generate
		genvar ii;
		for (ii = 0; ii < 4; ii = ii + 1) begin
			assign soc_flash_d[ii] = soc_flash_oeb[ii] ? 1'bz : soc_flash_out[ii];
		end
	endgenerate
 	assign gpio_in[5:2] = soc_flash_d;

	spiflash spiflash_i (
		.csb(soc_flash_csn),
		.clk(soc_flash_clk),
		.io0(soc_flash_d[0]),
		.io1(soc_flash_d[1]),
		.io2(soc_flash_d[2]),
		.io3(soc_flash_d[3])
	);

	wire soc_uart_0_tx = gpio_out[6];
	assign gpio_in[7] = 1'b1; // soc_uart_0_rx


	localparam ser_half_period = 109;
	event ser_sample;

	reg [7:0] buffer;

	always begin
		@(negedge soc_uart_0_tx);

		repeat (ser_half_period) @(posedge clk);
		-> ser_sample; // start bit

		repeat (8) begin
			repeat (ser_half_period) @(posedge clk);
			repeat (ser_half_period) @(posedge clk);
			buffer = {soc_uart_0_tx, buffer[7:1]};
			-> ser_sample; // data bit
		end

		repeat (ser_half_period) @(posedge clk);
		repeat (ser_half_period) @(posedge clk);
		-> ser_sample; // stop bit

		if (buffer < 32 || buffer >= 127)
			$display("Serial data: %d", buffer);
		else
			$display("Serial data: '%c'", buffer);
	end

endmodule