module lutram_tb;

    localparam K = 4;
    reg frame_strobe = 0;
    reg [2**K:0] frame_data = {1'b1, 16'h5555};
    reg write_clk = 0;
    reg write_en = 0;
    reg [K-1:0] write_addr = 0;
    reg write_data = 0;

    reg [K-1:0] lut_i = 0;
    wire lut_o;

    lutram #(.K(K)) uut (
        .frame_strobe(frame_strobe), .frame_data(frame_data),
        .write_clk(write_clk), .write_en(write_en), .write_addr(write_addr), .write_data(write_data),
        .lut_i(lut_i), .lut_o(lut_o)
    );

    initial begin
        $dumpfile("lutram_tb.vcd");
        $dumpvars(0, lutram_tb);
        frame_strobe = 0; #10; frame_strobe = 1; #10; frame_strobe = 0; #10; // initial configuration
        lut_i = 1; #10; lut_i = 2; #10; lut_i = 3; #10; // basic LUT
        write_en = 1; write_data = 1; write_addr = 3; #10; // prepare write
        write_clk = 1; #10; write_clk = 0; #10; // execute write
        write_en = 1; write_data = 0; write_addr = 4; #10; // prepare write
        write_clk = 1; #10; write_clk = 0; #10; // execute write
        write_en = 1; write_data = 0; write_addr = 0; #10; // prepare write
        write_clk = 1; #10; write_clk = 0; #10; // execute write
        $finish;
    end
endmodule
