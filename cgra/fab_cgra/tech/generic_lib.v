`ifndef UNIT_DELAY
`define UNIT_DELAY #1
`endif

module generic_lat(input wire d, e, output reg q, qn);
    always @* begin
        q <= `UNIT_DELAY d;
        qn <= `UNIT_DELAY ~d;
    end
endmodule

module generic_mux2(input wire i0, i1, s0, output wire y);
    assign `UNIT_DELAY y = s0 ? i1 : i0;
endmodule

module generic_mux4(input wire i0, i1, i2, i3, s0, s1, output wire y);
    wire a0 = s0 ? i1 : i0;
    wire a1 = s0 ? i3 : i2;
    assign `UNIT_DELAY y = s1 ? a1 : a0;
endmodule

module generic_mux8(input wire i0, i1, i2, i3, i4, i5, i6, i7, s0, s1, s2, output wire y);
    wire a0 = s0 ? i1 : i0;
    wire a1 = s0 ? i3 : i2;
    wire a2 = s0 ? i5 : i4;
    wire a3 = s0 ? i7 : i6;
    wire b0 = s1 ? a1 : a0;
    wire b1 = s1 ? a3 : a2;
    assign `UNIT_DELAY y = s1 ? b1 : b0;
endmodule

module generic_mux16(input wire i0, i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13, i14, i15,
    s0, s1, s2, s3,
    output wire y);
    wire a0, a1;
    generic_mux8 m0(.i0(i0), .i1(i1), .i2(i2), .i3(i3), .i4(i4), .i5(i5), .i6(i6), .i7(i7), .s0(s0), .s1(s1), .s2(s2), .y(a0));
    generic_mux8 m1(.i0(i8), .i1(i9), .i2(i10), .i3(i11), .i4(i12), .i5(i13), .i6(i14), .i7(i15), .s0(s0), .s1(s1), .s2(s2), .y(a1));
    assign `UNIT_DELAY y = s3 ? a1 : a0;
endmodule

module generic_and(input wire a, b, output wire y);
    assign `UNIT_DELAY y = a & b;
endmodule

module generic_buf(input wire a, output wire y);
    assign y = a;
endmodule

module generic_clkbuf(input wire a, output wire y);
    assign y = a;
endmodule

module generic_dff(input clk, d, output reg q);
    always @(posedge clk)
        q <= d;
endmodule

module generic_dffrs(input clk, d, rn, sn, output reg q);
    always @(posedge clk, negedge rn, negedge sn)
        if (!rn)
            q <= 0;
        else if (!sn)
            q <= 1;
        else
            q <= d;
endmodule
