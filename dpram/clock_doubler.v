`timescale 1ns/1ps

module clock_doubler(input clk, output clkx2);

localparam DEL = 4;
wire [DEL:0] delay_line;

assign delay_line[0] = clk;

genvar ii;
for (ii = 0; ii < DEL; ii = ii + 1'b1) begin: bufs
	(* keep *) BUF buf_i (.A(delay_line[ii]), .Q(delay_line[ii + 1]));
end

(* keep *) XOR xor_i(.A(clk), .B(delay_line[DEL]), .Q(clkx2));

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
