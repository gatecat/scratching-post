module logic_cell(
	input CLK,
	input [2:0] cfg_strb,
	input [2:0] cfg_data,
	input T, L, R, B,
	output Q
);

	// config storage
	wire [8:0] cfg;
	generate
	genvar ii, jj;
		for (ii = 0; ii < 3; ii = ii + 1'b1)
			for (jj = 0; jj < 3; jj = jj + 1'b1)
				sky130_fd_sc_hd__dlxtn_1 cfg_lat_i (
					.D(cfg_data[jj]),
					.GATE_N(cfg_strb[ii]),
					.Q(cfg[ii*3 + jj])
				);
	endgenerate

	wire i0, i1;
	// I input muxes
	sky130_fd_sc_hd__mux4_1 i0mux (
		.A0(1'b0), .A1(T), .A2(R), .A3(L),
		.S0(cfg[0]), .S1(cfg[1]),
		.X(i0)
	);
	sky130_fd_sc_hd__mux4_1 i1mux (
		.A0(1'b1), .A1(B), .A2(R), .A3(L),
		.S0(cfg[3]), .S1(cfg[4]),
		.X(i1)
	);
	// S input mux
	wire s0s, s0c, s0;
	sky130_fd_sc_hd__mux4_1 smux (
		.A0(T), .A1(R), .A2(L), .A3(B),
		.S0(cfg[2]), .S1(cfg[5]),
		.X(s0s)
	);
	// S constant
	sky130_fd_sc_hd__nand2_1 sconst (
		.A(s0s), .B(cfg[6]), .Y(s0c)
	);
	// S invert
	sky130_fd_sc_hd__xnor2_1 sinv (
		.A(s0c), .B(cfg[7]), .Y(s0)
	);
	// The logic element
	wire muxo_n;
	sky130_fd_sc_hd__mux2i_1 lmux (
		.A0(i0), .A1(i1), .S(s0), .Y(muxo_n)
	);
	// The DFF
	wire dffo_n;
	sky130_fd_sc_hd__dfsbp_1 dff(
		.D(muxo_n),
		.SET_B(cfg_strb[0]),
		.CLK(CLK),
		.Q(dffo_n)
	);
	// The final output mux
	sky130_fd_sc_hd__mux2i_1 ffsel (
		.A0(muxo_n), .A1(dffo_n), .S(cfg[8]), .Y(Q)
	);
endmodule
