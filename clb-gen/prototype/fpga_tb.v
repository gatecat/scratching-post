module fpga_tb;

    localparam W = 3;
    localparam H = 4;
    localparam FW = 4*W;
    localparam FH = 2*H;

    reg [FW-1:0] bitstream [0:FH-1];
    reg cfg_mode = 1'b0;
    reg cfg_frameinc = 1'b0;
    reg cfg_framestrb = 1'b0;
    reg cfg_dataclk = 1'b0;
    reg [3:0] cfg_sel = 4'b0;

    integer i, j;

    reg [6:0] gpio_in;
    wire [7:0] io_out;

    initial begin
        $dumpfile("fpga_tb.vcd");
        $dumpvars(0, fpga_tb);
        $readmemb("bitstream.txt", bitstream);
        #5;
        cfg_mode = 1'b1;
        #5;
        // clear FDR
        cfg_frameinc = 1'b1;
        #5;
        cfg_frameinc = 1'b0;
        #5;
        // reset FAR
        cfg_mode = 1'b0;
        #5;
        cfg_mode = 1'b1;
        #5;
        for (i = 0; i < FH; i = i + 1'b1) begin
            for (j = 0; j < FW; j = j + 1'b1) begin
                if (bitstream[i][j]) begin
                    cfg_sel = j;
                    #5;
                    cfg_dataclk = 1'b1;
                    #5;
                    cfg_dataclk = 1'b0;
                    #5;
                end
            end
            cfg_framestrb = 1'b1;
            #5;
            cfg_framestrb = 1'b0;
            #5;
            cfg_frameinc = 1'b1;
            #5;
            cfg_frameinc = 1'b0;
            #5;
        end
        #5;
        cfg_mode = 1'b0;
        #5;
        for (i = 0; i < 128; i = i + 1'b1) begin
            gpio_in = i;
            #5;
        end
        $finish;
    end

    wire [7:0] io_in = {cfg_mode ? {cfg_sel, cfg_dataclk, cfg_framestrb, cfg_frameinc} : gpio_in, cfg_mode};
    user_module_341404507891040852 dut_i(.io_in(io_in), .io_out(io_out));

endmodule
