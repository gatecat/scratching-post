module MULADDB_impl #(
    parameter A_WIDTH = 8,
    parameter B_WIDTH = 8,
    parameter C_WIDTH = 20,
    parameter Q_WIDTH = 20
) (
    // configuration
    input A_reg, B_reg, C_reg,
    input ACC, signExtension, ACCout,
    // data
    input [A_WIDTH-1:0] A,
    input [B_WIDTH-1:0] B,
    input [C_WIDTH-1:0] C,
    input clr,
    input CLK,
    output [Q_WITDH-1:0] Q
);
    reg [A_WIDTH-1:0] A_q;
    reg [B_WIDTH-1:0] B_q;
    wire [A_WIDTH-1:0] OPA = A_reg ? A_q : A;
    wire [B_WIDTH-1:0] OPB = B_reg ? B_q : B;

    localparam M_WIDTH = A_WIDTH + B_WIDTH;
    wire [M_WIDTH-1:0] OPAE = {{(M_WIDTH-A_WIDTH){signExtension ? OPA[A_WIDTH-1] : 1'b0}},OPA};
    wire [M_WIDTH-1:0] OPBE = {{(M_WIDTH-B_WIDTH){signExtension ? OPB[B_WIDTH-1] : 1'b0}},OPB};
    wire [M_WIDTH-1:0] M = OPAE * OPBE;

    always @(posedge CLK) begin
        A_q <= A;
        B_q <= B;
    end

    generate
    if (C_WIDTH > 0) begin
        reg [C_WIDTH-1:0] C_q;
        reg [Q_WIDTH-1:0] ACC_q;
        wire [C_WIDTH-1:0] OPC = C_reg ? C_q : C;
        wire [C_WIDTH-1:0] sum_in = ACC ? ACC_q : OPC;

        wire [Q_WIDTH-1:0] M_ext = {{(Q_WIDTH-M_WIDTH){signExtension ? M[M_WIDTH-1] : 1'b0}},M};
        wire [Q_WIDTH-1:0] sum = M_ext + sum_in;

        always @(posedge CLK) begin
            C_q <= C;
            ACC_q <= clr ? 0 : sum;
        end
        assign Q = ACCout ? ACC_q : sum;
    end else begin
        assign Q = M;
    end
    endgenerate
endmodule
