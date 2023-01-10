module top(input wire clk, input wire [27:0] io_in, output wire [27:0] io_out, io_oeb);
	localparam I = 1;
	localparam N = 2**I;
	localparam J = 3;
	localparam M = 2**J;
	localparam W1 = 3;
	localparam W2 = 7;

	wire [W1-1:0] wr_data = io_in[0 +: W1];
	wire a_wren = io_in[W1];
	wire b_wren = io_in[W1+1];
	wire [J-1:0] sel0 = io_in[W1+2 +: J];
	wire [I-1:0] sel1 = io_in[W1+J+2 +: I];

	reg [W2-1:0] result[0:N-1];

	generate
		genvar ii, jj;
		for (ii = 0; ii < N; ii = ii + 1'b1) begin: outer
			reg [W1-1:0] A[0:M-1];
			reg [W1-1:0] B[0:M-1];
			reg [2*W1-1:0] P[0:M-1];
			for (jj = 0; jj < M; jj = jj + 1'b1) begin: inner
				always @(posedge clk) begin
					if (sel1 == ii && sel0 == jj) begin
						if (a_wren) A[jj] <= wr_data;
						if (b_wren) B[jj] <= wr_data;
					end
					P[jj] <= A[jj] * B[jj];
				end
			end
			integer j;
			reg [W2-1:0] tmp;
			always @(posedge clk) begin
				tmp = 0;
				for (j = 0; j < M; j = j + 1'b1)
					tmp = tmp + P[j];
				result[ii] <= tmp;
			end
		end
	endgenerate

	assign io_out = result[sel1];

	assign io_oeb = 28'b0;
endmodule
