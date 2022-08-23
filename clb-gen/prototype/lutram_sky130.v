`default_nettype none
module lutram #(parameter K=4) (
	input wire frame_strobe,
	input wire [2**K:0] frame_data, // {lut_mode[0], lut_init[W-1:0]}
	input wire write_clk,
	input wire write_en,
	input wire [K-1:0] write_addr,
	input wire write_data,

	input wire [K-1:0] lut_i,
	output wire lut_o
);
	localparam W=2**K;
	wire [W-1:0] lut_data;

	wire lutram_mode, write_strobe;

	// LUTRAM mode config and write pulse gen
	sky130_fd_sc_hd__dlxtp_1 mode_lat_i (
		.D(frame_data[W]),
		.GATE(frame_strobe),
		.Q(lutram_mode)
	);

	write_pulse_gen pulse_gen_i (
		.clk(write_clk),
		.en(write_en & lutram_mode),
		.q(write_strobe)
	);

	// Storage array
	generate
		genvar ii;
		for (ii = 0; ii < W; ii = ii + 1'b1) begin: lut_loop
			wire bit_sel = (write_addr == ii);
			wire bit_strobe = (bit_sel & write_strobe) | frame_strobe;
			wire bit_d = frame_strobe ? frame_data[ii] : write_data;
			sky130_fd_sc_hd__dlxtp_1 bit_cell_i (
				.D(bit_d),
				.GATE(bit_strobe),
				.Q(lut_data[ii])
			);
		end
	endgenerate

	// LUT output mux
	assign lut_o = lut_data[lut_i];
endmodule

module write_pulse_gen(input wire clk, input wire en, output wire q);
`ifdef SYNTHESIS
	wire clk_del, clk_strb;
	sky130_fd_sc_hd__dlymetal6s6s_1 dly_i (.A(clk), .X(clk_del));
	sky130_fd_sc_hd__and2b_1 cmp_i (.A_N(clk_del), .B(clk), .X(clk_strb));
	sky130_fd_sc_hd__and2_2 gate_i (.A(clk_strb), .B(en), .X(q));
`else
	reg clk_del, strb_out;
	always @* clk_del = #3 clk;
	always @* strb_out = #1 (en & (clk & ~clk_del));
	assign q = strb_out;
`endif
endmodule

`ifndef SYNTHESIS
module sky130_fd_sc_hd__dlxtp_1(input D, GATE, output reg Q);
	always @(*) if (GATE) Q <= D;
endmodule
`endif
