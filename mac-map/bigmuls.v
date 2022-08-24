module top(input wire signed [9:0] A, B, output wire signed [19:0] X);
	assign X = A*B;
endmodule
