module user_project_core(input [37:0] io_in, output [37:0] io_out, io_oeb);

wire [37:0] io_out_buf, io_oeb_buf;
generate
	genvar ii;
	for (ii = 0; ii < 38; ii = ii + 1'b1) begin: bufs
		(* keep *) buf_x2 out_buf (.i(io_out_buf[ii]), .q(io_out[ii]));
		(* keep *) buf_x2 oeb_buf (.i(io_oeb_buf[ii]), .q(io_oeb[ii]));
	end
endgenerate

wire clk;              // CPU clock 
wire reset;            // reset signal
wire [15:0] A;        // address bus
wire [7:0] DI;         // data in, read bus
wire [7:0] DO;        // data out, write bus
wire WE;              // write enable
wire IRQ;              // interrupt request
wire NMI;              // non-maskable interrupt request
wire RDY;              // Ready signal. Pauses CPU when RDY=0 

cpu MOS6502(
    .clk(clk), .reset(reset), .AB(A), .DI(DI), .DO(DO), .WE(WE),
    .IRQ(IRQ), .NMI(NMI), .RDY(RDY)
);

assign clk = io_in[0];
assign reset = io_in[1];
assign IRQ = io_in[2];
assign NMI = io_in[3];
assign RDY = io_in[4];
assign io_oeb_buf[4:0] = 5'b11111;

assign io_out_buf[20:5] = A;
assign io_oeb_buf[20:5] = {16{1'b0}};

assign DI = io_in[28:21];
assign io_out_buf[28:21] = DO;
assign io_oeb_buf[28:21] = {8{~WE}};

assign io_out_buf[37:29] = 0;
assign io_oeb_buf[37:29] = 0;

endmodule
