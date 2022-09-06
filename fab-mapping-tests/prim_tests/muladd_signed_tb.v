module testbench;

	reg [7:0] A, B;
	reg [19:0] C;
	reg CLK, clr;
	wire [19:0] Q;

	reg signed [19:0] Q_gold;

	localparam [0:0] OUT_SEL = 1'b0, EXT_MUL = 1'b1, ADD_IN_SEL = 1'b0, C_REG = 1'b0, B_REG = 1'b0, A_REG = 1'b0;

	task do_test;
		input signed [7:0] ia, ib;
		begin
			A = ia;
			B = ib;
			Q_gold = $signed(ia) * $signed(ib);
			#5;
			$display("gate=%d gold=%d", $signed(Q), Q_gold);
		end
	endtask

	initial begin
		C = 0;
		do_test(10, 10);
		do_test(10, -5);
		do_test(-5, -5);
		do_test(-1, -1);
		do_test(-128, -128);
		do_test(-128, 127);
	end

	MULADDA #(
		.ConfigBits({OUT_SEL, EXT_MUL, ADD_IN_SEL, C_REG, B_REG, A_REG})
	) dut (
		.A0(A[0]), .A1(A[1]), .A2(A[2]), .A3(A[3]), .A4(A[4]), .A5(A[5]), .A6(A[6]), .A7(A[7]),
		.B0(B[0]), .B1(B[1]), .B2(B[2]), .B3(B[3]), .B4(B[4]), .B5(B[5]), .B6(B[6]), .B7(B[7]),
		.C0(C[0]), .C1(C[1]), .C2(C[2]), .C3(C[3]), .C4(C[4]), .C5(C[5]), .C6(C[6]), .C7(C[7]), .C8(C[8]), .C9(C[9]), .C10(C[10]), .C11(C[11]), .C12(C[12]), .C13(C[13]), .C14(C[14]), .C15(C[15]), .C16(C[16]), .C17(C[17]), .C18(C[18]), .C19(C[19]),
		.Q0(Q[0]), .Q1(Q[1]), .Q2(Q[2]), .Q3(Q[3]), .Q4(Q[4]), .Q5(Q[5]), .Q6(Q[6]), .Q7(Q[7]), .Q8(Q[8]), .Q9(Q[9]), .Q10(Q[10]), .Q11(Q[11]), .Q12(Q[12]), .Q13(Q[13]), .Q14(Q[14]), .Q15(Q[15]), .Q16(Q[16]), .Q17(Q[17]), .Q18(Q[18]), .Q19(Q[19]),
		.clr(clr), .CLK(CLK)
	);

endmodule
