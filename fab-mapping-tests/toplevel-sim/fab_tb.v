`timescale 1ps/1ps
module fab_tb;
    wire [27:0] I_top;
    wire [27:0] T_top;
    reg [27:0] O_top = 0;
    wire [55:0] A_cfg, B_cfg;

    reg CLK = 1'b0;
    reg SelfWriteStrobe = 1'b0;
    reg [31:0] SelfWriteData = 1'b0;
    reg Rx = 1'b1;
    wire ComActive;
    wire ReceiveLED;
    reg s_clk = 1'b0;
    reg s_data = 1'b0;

    eFPGA_top top_i (
        .I_top(I_top),
        .T_top(T_top),
        .O_top(O_top),
        .A_config_C(A_cfg), .B_config_C(B_cfg),
        .CLK(CLK), .SelfWriteStrobe(SelfWriteStrobe), .SelfWriteData(SelfWriteData),
        .Rx(Rx),
        .ComActive(ComActive),
        .ReceiveLED(ReceiveLED),
        .s_clk(s_clk),
        .s_data(s_data)
    );

    localparam MAX_BITBYTES = 16384;
    reg [7:0] bitstream[0:MAX_BITBYTES-1];

    always #5000 CLK = (CLK === 1'b0);

    localparam UART_DIV = 8;

    task uart_send;
        input [7:0] data;
        reg [10:0] bits;
        begin
            bits = {2'b11, data, 1'b0}; // gap, stop, data, start
            for (j = 0; j < 11; j = j + 1'b1) begin
                Rx = bits[j];
                repeat (UART_DIV) @(posedge CLK);
            end
            Rx = 1'b1;
            repeat (UART_DIV) @(posedge CLK);
        end
    endtask

    integer i, j;
    initial begin
        $dumpfile("fab_tb.vcd");
        $dumpvars(0, fab_tb);
        $readmemh("bitstream.hex", bitstream);
        #10000;
        repeat (10) @(posedge CLK);
        #2500;
        for (i = 0; i < MAX_BITBYTES; i = i + 1'b1) begin
            uart_send(bitstream[i]);
        end
        repeat (100) @(posedge CLK);
        O_top = {28{1'b1}}; // reset will be one of these....
        repeat (5) @(posedge CLK);
        O_top = {28{1'b0}};
        repeat (500) @(posedge CLK);
        $finish;
    end

endmodule

module clk_buf(input A, output X);
assign X = A;
endmodule

