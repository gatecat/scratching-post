`default_nettype none
module lutnoram #(parameter K=4) (
	input wire frame_strobe,
	input wire [2**K-1:0] frame_data, // {lut_init[W-1:0]}

	input wire [K-1:0] lut_i,
	output wire lut_o
);
	localparam W=2**K;
	wire [W-1:0] lut_data;

	// Storage array
	generate
		genvar ii;
		for (ii = 0; ii < W; ii = ii + 1'b1) begin: lut_loop
			sky130_fd_sc_hd__dlxtp_1 bit_cell_i (
				.D(frame_data[ii]),
				.GATE(frame_strobe),
				.Q(lut_data[ii])
			);
		end
	endgenerate

	// LUT output mux
	assign lut_o = lut_data[lut_i];
endmodule

`ifndef SYNTHESIS
module sky130_fd_sc_hd__dlxtp_1(input D, GATE, output reg Q);
	always @(*) if (GATE) Q <= D;
endmodule
`endif
