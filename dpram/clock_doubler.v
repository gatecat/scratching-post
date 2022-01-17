`timescale 1ns/1ps

module clock_doubler(input clk, output clkx2);

localparam DEL = 20;
wire [DEL:0] delay_line;

assign delay_line[0] = clk;

genvar ii;
for (ii = 0; ii < DEL; ii = ii + 1'b1) begin: bufs
	(* keep *) BUF buf_i (.A(delay_line[ii]), .Q(delay_line[ii + 1]));
end

wire inv_dly_0, inv_dly_1;
wire pulse_0, pulse_1;


(* keep *) INV inv_0 (.A(delay_line[5]), .Q(inv_dly_0));
(* keep *) INV inv_1 (.A(delay_line[20]), .Q(inv_dly_1));

(* keep *) NAND pulse_gen_0 (.A(clk), .B(inv_dly_0), .Q(pulse_0));
(* keep *) NAND pulse_gen_1 (.A(delay_line[15]), .B(inv_dly_1), .Q(pulse_1));

(* keep *) NAND pulse_or (.A(pulse_0), .B(pulse_1), .Q(clkx2));

endmodule

module testbench;
	reg clk;
	always #10 clk = (clk === 1'b0);

	wire clkx2;

	initial begin
		$dumpfile("clock_doubler.vcd");
		$dumpvars(0, testbench);

		repeat (20) @(posedge clk);

		$finish;
	end

	clock_doubler dut(.clk(clk), .clkx2(clkx2));

endmodule
