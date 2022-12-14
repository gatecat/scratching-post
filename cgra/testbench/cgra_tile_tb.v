module testbench;

    localparam FW = 32; // bits per frame
    localparam FH = 2; // frames per tile
    localparam N = 12; // mul_width

    reg [FW-1:0] cfg_data = 1'b0;
    reg [FH-1:0] cfg_strb = 1'b0;
    reg clr = 1'b0;

    reg [N:0] N1END0 = 0, N1END1 = 0, S1END0 = 0, S1END1 = 0, W1END0 = 0, W1END1 = 0, E1END0 = 0, E1END1 = 0;
    wire [N:0] N1BEG0 = 0, N1BEG1 = 0, S1BEG0 = 0, S1BEG1 = 0, W1BEG0 = 0, W1BEG1 = 0, E1BEG0 = 0, E1BEG1 = 0;
    reg clk = 1'b0;

    cgra_mul_tile tile_i (
        .cfg_strbi(cfg_strb), .cfg_strbo(),
        .cfg_datai(cfg_data), .cfg_datao(),
        .CLRBEG(), .CLREND(clr),
        .N1BEG({N1BEG1, N1BEG0}), .N1END({N1END1, N1END0}),
        .S1BEG({S1BEG1, S1BEG0}), .S1END({S1END1, S1END0}),
        .E1BEG({E1BEG1, E1BEG0}), .E1END({E1END1, E1END0}),
        .W1BEG({W1BEG1, W1BEG0}), .W1END({W1END1, W1END0}),
        .clk(), .rst(), .gclocki(clk)
    );

    reg [FW-1:0] bitstream[0:FH-1];

    task do_test(input [11:0] a, b);
        begin
            E1END0 = {1'b1, a}; // todo: valid
            W1END1 = {1'b1, b};
            #5;
            clk = 1'b1;
            #10;
            clk = 1'b0;
            #5;
            $display("a=%d b=%d q=%d ar=%d", a, b, S1BEG1, S1BEG0);
        end
    endtask

    integer i;
    initial begin
        // load bitstream
        $readmemb("testbench/work/mul_and_route.bin", bitstream);
        #5;
        for (i = 0; i < FH; i = i + 1'b1) begin
            cfg_data = bitstream[i];
            #5;
            cfg_strb[i] = 1'b1;
            #5;
            cfg_strb[i] = 1'b0;
            #5;
        end
        do_test(10, 50);
    end

endmodule

