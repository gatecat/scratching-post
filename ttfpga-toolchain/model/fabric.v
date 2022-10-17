`default_nettype none

module fabric #(
    localparam W = 3,
    localparam H = 5,
    localparam FW = W * 4,
    localparam FH = H * 2
) (
  input fab_clk,
  input [FW*FH-1:0] cfg,
  input [3:0] io_in, 
  output [7:0] io_out
);

    wire [0:W-1] cell_q[0:H-1];
    generate
        genvar xx;
        genvar yy;
        for (yy = 0; yy < H; yy = yy + 1'b1) begin: y_c
            for (xx = 0; xx < W; xx = xx + 1'b1) begin: x_c
                wire ti, bi, li, ri;
                if (yy > 0) assign ti = cell_q[yy-1][xx]; else assign ti = io_in[xx];
                if (yy < H-1) assign bi = cell_q[yy+1][xx]; else assign bi = cell_q[yy][xx];
                if (xx > 0) assign li = cell_q[yy][xx-1]; else assign li = io_in[yy >= 4 ? 3 : yy];
                if (xx < W-1) assign ri = cell_q[yy][xx+1]; else assign ri = cell_q[yy][xx];
                logic_cell #(.has_ff(/*xx[0] ^ yy[0]*/1'b0)) lc_i (
                    .CLK(fab_clk),
                    .cfg({cfg[((yy * 2 + 1) * FW) + (xx * 4) +: 4], cfg[((yy * 2 + 0) * FW) + (xx * 4) +: 4]}),
                    .T(ti), .B(bi), .L(li),. R(ri),
                    .Q(cell_q[yy][xx])
                );
            end
        end
    endgenerate

    assign io_out = {cell_q[3][W-1], cell_q[2][W-1], cell_q[1][W-1], cell_q[0][W-1], cell_q[H-1][2], cell_q[H-1]};


endmodule

module logic_cell (
    input CLK,
    input [7:0] cfg,
    input T, L, R, B,
    output Q
);
    parameter has_ff = 1'b0;

    wire i0, i1;
    // I input muxes
    wire i0a, i0b;
    sky130_fd_sc_hd__nand2_1 i0muxa0 (
        .A(T), .B(cfg[0]),
        .Y(i0a)
    );
    sky130_fd_sc_hd__mux2i_1 i0muxa1 (
        .A0(R), .A1(L), .S(cfg[0]),
        .Y(i0b)
    );

    sky130_fd_sc_hd__mux2i_1 i0muxb (
        .A0(i0a), .A1(i0b), .S(cfg[1]),
        .Y(i0)
    );

    wire i1a, i1b;
    sky130_fd_sc_hd__and2_1 i1muxa0 (
        .A(cfg[2]), .B(L),
        .X(i1a)
    );
    sky130_fd_sc_hd__mux2i_1 i1muxa1 (
        .A0(B), .A1(R), .S(cfg[2]),
        .Y(i1b)
    );
    sky130_fd_sc_hd__mux2i_1 i1muxb (
        .A0(i1a), .A1(i1b), .S(cfg[3]),
        .Y(i1)
    );
    // S input mux
    wire s0s, s0, s0a, s0b;

    sky130_fd_sc_hd__nand2_1 s0muxa0 (
        .A(T), .B(cfg[4]),
        .Y(s0a)
    );
    sky130_fd_sc_hd__mux2i_1 s0muxa1 (
        .A0(R), .A1(L), .S(cfg[4]),
        .Y(s0b)
    );

    sky130_fd_sc_hd__mux2i_1 s0muxb (
        .A0(s0a), .A1(s0b), .S(cfg[5]),
        .Y(s0s)
    );
    // S invert
    sky130_fd_sc_hd__xnor2_1 sinv (
        .A(s0s), .B(cfg[6]), .Y(s0)
    );
    // The logic element
    wire muxo_n;
    sky130_fd_sc_hd__mux2i_1 lmux (
        .A0(i0), .A1(i1), .S(s0), .Y(muxo_n)
    );
    // The DFF
    generate if (has_ff) begin: dff
        wire dffo_n;
        sky130_fd_sc_hd__dfsbp_1 dff(
            .D(muxo_n),
            .SET_B(1'b1),
            .CLK(CLK),
            .Q(dffo_n)
        );
        // The final output mux
        sky130_fd_sc_hd__mux2i_1 ffsel (
            .A0(muxo_n), .A1(dffo_n), .S(cfg[7]), .Y(Q)
        );
    end else begin
        sky130_fd_sc_hd__inv_1 linv (
            .A(muxo_n), .Y(Q)
        );
    end
    endgenerate
endmodule
