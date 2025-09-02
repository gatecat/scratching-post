// The purpose of this wrapper is to break out the combined ports to something more user-friendly

module sim_top(
	input clk,
	input rst_n,

	output soc_flash_clk,
	output soc_flash_csn,
	output [3:0] soc_flash_d_o,
	output [3:0] soc_flash_d_oe,
	input [3:0] soc_flash_d_i,

	output [7:0] gpio_0_gpio_o,
	output [7:0] gpio_0_gpio_oe,
	input [7:0] gpio_0_gpio_i,

	output [3:0] gpio_open_drain_gpio_o,
	output [3:0] gpio_open_drain_gpio_oe,
	input [3:0] gpio_open_drain_gpio_i,

	input soc_uart_0_rx,
	output soc_uart_0_tx
);

	wire [43:0] gpio_in, gpio_oeb, gpio_out;

	openframe_project_wrapper dut (
		.gpio_in(gpio_in),
		.gpio_oeb(gpio_oeb),
		.gpio_out(gpio_out)
	);

	assign gpio_in[38] = clk;
	assign gpio_in[40] = rst_n;

	assign soc_flash_clk = gpio_out[0];
	assign soc_flash_csn = gpio_out[1];
	assign soc_flash_d_o = gpio_out[5:2];
	assign soc_flash_d_oe = ~gpio_oeb[5:2];
	assign gpio_in[5:2] = soc_flash_d_i;

	assign gpio_0_gpio_o = gpio_out[15:8];
	assign gpio_0_gpio_oe = ~gpio_oeb[15:8];
	assign gpio_in[15:8] = gpio_0_gpio_i;

	assign gpio_open_drain_gpio_o = gpio_out[28:25];
	assign gpio_open_drain_gpio_oe = ~gpio_oeb[28:25];
	assign gpio_in[28:25] = gpio_open_drain_gpio_i;

	assign gpio_in[7] = soc_uart_0_rx;
	assign soc_uart_0_tx = gpio_in[6];
endmodule

