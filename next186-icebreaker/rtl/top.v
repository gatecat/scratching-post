module top(
    input wire CLK,

    output wire TX,
    input wire RX,

    input wire BTN_N,
    output wire LEDR_N,
    output wire LEDG_N,

    output wire LED1, LED2, LED3, LED4, LED5,
    input wire BTN1, BTN2, BTN3
);

    reg [7:0] por_ctr = 0;
    reg resetn = 1'b0;
    wire reset = ~resetn;

    always @(posedge CLK) begin
        if (!BTN_N)
            por_ctr <= 0;
        else if (!(&por_ctr))
            por_ctr <= por_ctr + 1'b1;
        resetn <= &por_ctr;
    end 

    wire [20:0] ADDR;
    wire [15:0] PORT_ADDR;
    wire [15:0] DIN, DOUT, POUT;
    wire CPU_CE;

    wire MREQ, IORQ, INTA, WR, WORD, LOCK;

    wire [20:0] IADDR;
    wire [47:0] INSTR;
    wire IFETCH, FLUSH, HALT;
    wire [2:0] ISIZE;

    Next186_CPU cpu (
        .ADDR(ADDR),          // mem address
        .PORT_ADDR(PORT_ADDR),    // port address
        .DIN(DIN),        // mem/port data in
        .DOUT(DOUT),  // mem data out
        .POUT(POUT),  // port data out
        .FAKE286(1'b0),
        .CLK(CLK),
        .CE(CPU_CE),
        .INTR(1'b0),
        .NMI(1'b0),
        .RST(reset),
        .MREQ(MREQ),
        .IORQ(IORQ),
        .INTA(INTA),
        .WR(WR),
        .WORD(WORD),
        .LOCK(LOCK),
        .IADDR(IADDR),
        .INSTR(INSTR),
        .IFETCH(IFETCH),
        .FLUSH(FLUSH),
        .ISIZE(ISIZE),
        .HALT(HALT)
    );

    wire [31:0] RAM_DIN, RAM_DOUT;
    wire [18:0] RAM_ADDR;
    wire RAM_MREQ;
    wire RAM_RD, RAM_WR;
    wire [3:0] RAM_WMASK;


    BIU186_32bSync_2T_DelayRead biu (
        .CLK(CLK),
        .INSTR(INSTR),
        .ISIZE(ISIZE),
        .IFETCH(IFETCH),
        .FLUSH(FLUSH),
        .MREQ(MREQ),
        .WR(WR),
        .WORD(WORD),
        .ADDR(ADDR),
        .IADDR(IADDR),
        .CE186(CPU_CE),   // CPU clock enable
        .RAM_DIN(RAM_DIN),
        .RAM_DOUT(RAM_DOUT),
        .RAM_ADDR(RAM_ADDR),
        .RAM_MREQ(RAM_MREQ),
        .RAM_WMASK(RAM_WMASK),
        .DOUT(DOUT),
        .DIN(DIN),
        .CE(resetn),       // BIU clock enable
        .data_bound(),
        .WSEL({~ADDR[0], ADDR[0]}),    // normally {~ADDR[0], ADDR[0]}
        .RAM_RD(RAM_RD),
        .RAM_WR(RAM_WR),
        .IORQ(IORQ),
        .FASTIO(1'b0)
    );

    reg [31:0] rom[0:63];
    reg [31:0] rom_dout;
    wire rom_sel = (RAM_ADDR[18:6] == 0);
    reg rom_rdsel;
    initial $readmemh("rom.hex", rom);

    always @(posedge CLK) begin
        rom_dout <= rom[RAM_ADDR[5:0]];
        rom_rdsel <= rom_sel;

    end

    reg [31:0] ram[0:255];
    reg [31:0] ram_dout;

    always @(posedge CLK) begin
        if (RAM_MREQ && RAM_WR && !rom_sel) begin
            if (RAM_WMASK[0]) ram[RAM_ADDR[7:0]][7:0] <= RAM_DOUT[7:0];
            if (RAM_WMASK[1]) ram[RAM_ADDR[7:0]][15:8] <= RAM_DOUT[15:8];
            if (RAM_WMASK[2]) ram[RAM_ADDR[7:0]][23:16] <= RAM_DOUT[23:16];
            if (RAM_WMASK[3]) ram[RAM_ADDR[7:0]][31:24] <= RAM_DOUT[31:24];
        end else if (RAM_RD) begin
            ram_dout <= ram[RAM_ADDR[7:0]];
        end
        rom_rdsel <= (RAM_ADDR[18:6] == 0);

    end

    assign RAM_DIN = rom_rdsel ? {rom_dout[7:0], rom_dout[15:8], rom_dout[23:16], rom_dout[31:24]} : ram_dout;

    reg [7:0] io = 0;

    always @(posedge CLK) begin
        if (IORQ && WR)
            io <= POUT[7:0];
    end

    assign LEDR_N = ~io[0];
    assign LEDG_N = ~io[1];

endmodule
