module top(input clk, we, input [4:0] aw, aa, ab, input [3:0] wd, output reg [3:0] ra, rb);
	reg [3:0] mem[0:31];
	always @(posedge clk)
		if (we) mem[aw] <= wd;
	always @(posedge clk)
		ra <= mem[aa];
	always @(posedge clk)
		rb <= mem[ab];
endmodule
