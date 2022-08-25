`define PRIM_WIDTH 8

/*
We can't use the built-in Yosys decomposition rules for decomposing multiplies
because they assume DSPs are either configurable signedness or signed-only.
Current gen FABulous DSPs are unsigned-only, future revisions will hopefully
have configurable signedness but this suffices for now.
*/
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
    if (A_SIGNED || B_SIGNED) begin : s2u
        // TODO: is there a better way of converting signed to unsigned?
        wire a_sign = A_SIGNED ? A[A_WIDTH-1] : 1'b0;
        wire b_sign = B_SIGNED ? B[B_WIDTH-1] : 1'b0;
        wire [A_WIDTH-1:0] a_u = a_sign ? -A : A;
        wire [B_WIDTH-1:0] b_u = b_sign ? -B : B;
        wire [Y_WIDTH-1:0] y_u;
        \$mul #(
            .A_SIGNED(1'b0),
            .B_SIGNED(1'b0),
            .A_WIDTH(A_WIDTH),
            .B_WIDTH(B_WIDTH),
            .Y_WIDTH(Y_WIDTH),
        ) _TECHMAP_REPLACE_ (
            .A(a_u), .B(b_u), .Y(y_u)
        );
        // pos*pos -> pos; neg*pos -> neg; neg*neg -> pos
        assign Y = (a_sign ^ b_sign) ? -y_u : y_u;
    end else if (A_WIDTH > `PRIM_WIDTH || B_WIDTH > `PRIM_WIDTH)  begin : extend
        // make A the bigger one to keep things simple
        if (B_WIDTH > A_WIDTH) begin : swizzle
            \$mul #(
                .A_SIGNED(1'b0),
                .B_SIGNED(1'b0),
                .A_WIDTH(B_WIDTH),
                .B_WIDTH(A_WIDTH),
                .Y_WIDTH(Y_WIDTH),
            ) _TECHMAP_REPLACE_ (
                .A(B), .B(A), .Y(Y)
            );
        end else begin : split
            // this probably isn't optimal...
            // a*b (2*8ah + al)b = 2*8ahb + alb
            wire [A_WIDTH-`PRIM_WIDTH-1:0] ah = A[A_WIDTH-1:`PRIM_WIDTH];
            wire [`PRIM_WIDTH-1:0] al = A[`PRIM_WIDTH-1:0];
            wire [B_WIDTH+A_WIDTH-`PRIM_WIDTH-1:0] yh;
            wire [B_WIDTH+`PRIM_WIDTH-1:0] yl;
            \$mul #(
                .A_SIGNED(1'b0),
                .B_SIGNED(1'b0),
                .A_WIDTH(A_WIDTH-`PRIM_WIDTH),
                .B_WIDTH(B_WIDTH),
                .Y_WIDTH(B_WIDTH+A_WIDTH-`PRIM_WIDTH)
            ) mulh (
                .A(ah), .B(B), .Y(yh)
            );
            \$mul #(
                .A_SIGNED(1'b0),
                .B_SIGNED(1'b0),
                .A_WIDTH(`PRIM_WIDTH),
                .B_WIDTH(B_WIDTH),
                .Y_WIDTH(B_WIDTH+`PRIM_WIDTH),
            ) mull (
                .A(al), .B(B), .Y(yl)
            );
            assign Y = {yh, {`PRIM_WIDTH{1'b0}}} + yl; 
        end
    end else begin
        wire _TECHMAP_FAIL_ = 1'b1;
    end
    endgenerate
endmodule
