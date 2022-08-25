module top(input wire [7:0] A, B, input wire [15:0] C, output wire [15:0] X);
	wire [15:0] P = A * B;
	assign X = P + C;
endmodule
