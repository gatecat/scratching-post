(* techmap_celltype = "$mul" *)
module _80_mul (A, B, Y);
	parameter A_SIGNED = 0;
	parameter B_SIGNED = 0;
	parameter A_WIDTH = 1;
	parameter B_WIDTH = 1;
	parameter Y_WIDTH = 1;
	(* force_downto *)
	input [A_WIDTH-1:0] A;
	(* force_downto *)
	input [B_WIDTH-1:0] B;
	(* force_downto *)
	output [Y_WIDTH-1:0] Y;

	generate
		if (A_SIGNED || B_SIGNED || A_WIDTH > 8 || B_WIDTH > 8)
			wire _TECHMAP_FAIL_ = 1; // TODO: fake signedness, decomposition
	endgenerate

	wire [7:0] Ae = A;
	wire [7:0] Be = B;
	wire [15:0] Q;

	// no registers, no accumulator, no sign extended product
	MULADD #(
		.ConfigBits(6'b000000)
	) _TECHMAP_REPLACE_ (
		.A7(Ae[7]), .A6(Ae[6]), .A5(Ae[5]), .A4(Ae[4]), .A3(Ae[3]), .A2(Ae[2]), .A1(Ae[1]), .A0(Ae[0]), 
		.B7(Be[7]), .B6(Be[6]), .B5(Be[5]), .B4(Ae[4]), .B3(Be[3]), .B2(Be[2]), .B1(Be[1]), .B0(Be[0]), 
		.C19(1'b0), .C18(1'b0), .C17(1'b0), .C16(1'b0), .C15(1'b0), .C14(1'b0), .C13(1'b0), .C12(1'b0), .C11(1'b0), .C10(1'b0), .C9(1'b0), .C8(1'b0), .C7(1'b0), .C6(1'b0), .C5(1'b0), .C4(1'b0), .C3(1'b0), .C2(1'b0), .C1(1'b0), .C0(1'b0),
		.Q15(Q[15]), .Q14(Q[14]), .Q13(Q[13]), .Q12(Q[12]), .Q11(Q[11]), .Q10(Q[10]), .Q9(Q[9]), .Q8(Q[8]), .Q7(Q[7]), .Q6(Q[6]), .Q5(Q[5]), .Q4(Q[4]), .Q3(Q[3]), .Q2(Q[2]), .Q1(Q[1]), .Q0(Q[0])
	);

	assign Y = Q[Y_WIDTH-1:0];

endmodule
