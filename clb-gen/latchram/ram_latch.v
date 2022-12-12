module ram_blk #(parameter A=5, D=8, P=1)(input WSTB, input [A-1:0] WA, input [D-1:0] WD, input [A*P-1:0] RA, output [D*P-1:0] RD);
	wire [D-1:0] ram[0:2**A-1];

	generate
		genvar ii, jj;

		for (ii = 0; ii < 2**A; ii = ii + 1'b1) begin:word
			wire word_strbn;
			sky130_fd_sc_hd__nand2_1 we_gen_i (
				.A(WA == ii),
				.B(WSTB),
				.Y(word_strbn)
			);
			for (jj = 0; jj < D; jj = jj + 1'b1) begin:bits
				sky130_fd_sc_hd__dlxtn_1 rfbit_i (
					.GATE_N(word_strbn),
					.D(WD[jj]),
					.Q(ram[ii][jj])
				);
			end
		end
	endgenerate

	generate
		genvar ii;
		for (ii = 0; ii < P; ii = ii + 1'b1)
			assign RD[D*ii +: D] = ram[RA[A*ii +: A]];
	endgenerate

endmodule
