module ram_blk #(parameter A=5, D=4, P=2)(input WSTB, input [A-1:0] WA, input [D-1:0] WD, input [A*P-1:0] RA, output [D*P-1:0] RD);
	reg [D-1:0] ram[0:2**A-1];
	always @(posedge WSTB) begin
		ram[WA] <= WD;
	end
	generate
		genvar ii;
		for (ii = 0; ii < P; ii = ii + 1'b1)
			assign RD[D*ii +: D] = ram[RA[A*ii +: A]];
	endgenerate
endmodule
