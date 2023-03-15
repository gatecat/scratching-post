`timescale 1 ns / 1 ps

module xilinx_zcu104_tb;
reg clk = 1'b0;

always #10 clk = (clk === 1'b0);

wire clk_p = clk, clk_n = ~clk;
wire cpu_reset = 1'b0;
wire serial_tx;

xilinx_zcu104 dut_i (
	.clk125_p(clk_p),
	.clk125_n(clk_n),
	.cpu_reset(cpu_reset),
	.serial_cts(1'b1),
	.serial_rts(1'b1),
	.serial_tx(serial_tx),
	.serial_rx(1'b1),
	.jtag_pmod0_tck(1'b0),
	.jtag_pmod0_tms(1'b0),
	.jtag_pmod0_tdi(1'b0),
	.jtag_pmod0_tdo()
);


	initial begin
		$dumpfile("testbench.vcd");
		$dumpvars(0, xilinx_zcu104_tb);

		$display("Start running...");
		repeat (1000) begin
			repeat (50000) @(posedge clk);
			$display("+50000 cycles");
		end
		$finish;
	end

endmodule
