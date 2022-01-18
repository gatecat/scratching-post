module user_project_core(input [37:0] io_in, output [37:0] io_out, io_oeb);

wire [37:0] io_out_buf, io_oeb_buf;
generate
	genvar ii;
	for (ii = 0; ii < 38; ii = ii + 1'b1) begin: bufs
		(* keep *) buf_x2 out_buf (.i(io_out_buf[ii]), .q(io_out[ii]));
		(* keep *) buf_x2 oeb_buf (.i(io_oeb_buf[ii]), .q(io_oeb[ii]));
	end
endgenerate

// To prevent things being optimised away; before we have a real SoC rather than just a PnR test; create a big shift register for the inputs/outputs

wire clk = io_in[0];
wire reset = io_in[1];
wire we = io_in[2];
wire shift = io_in[3];
wire latch = io_in[4];

assign io_oeb_buf[4:0] = 5'b11111;
assign io_oeb_buf[36:5] = {32{we}};

assign io_out_buf[4:0] = 5'b00000;
assign io_oeb_buf[37] = 1'b0;
assign io_out_buf[37] = 1'b0;

reg [133:0] input_sr, input_lat;
wire [147:0] output_d;
reg [147:0] output_sr;

always @(posedge clk) begin
	if (shift && we) begin
		input_sr <= {input_sr[101:0], io_in[36:5]};
	end
	if (shift && !we) begin
		output_sr <= {32'b0, output_sr[147:32]};
	end
	if (latch) begin
		input_lat <= input_sr;
		output_sr <= output_d;
	end
end

assign io_out_buf[36:5] = output_sr[31:0];

VexRiscv vex_i (
  .externalResetVector(input_lat[31:0]),
  .timerInterrupt(input_lat[32]),
  .softwareInterrupt(input_lat[33]),
  .externalInterruptArray(input_lat[65:34]),
  .iBusWishbone_CYC(output_d[0]),
  .iBusWishbone_STB(output_d[1]),
  .iBusWishbone_ACK(input_lat[66]),
  .iBusWishbone_WE(output_d[2]),
  .iBusWishbone_ADR(output_d[32:3]),
  .iBusWishbone_DAT_MISO(input_lat[98:67]),
  .iBusWishbone_DAT_MOSI(output_d[64:33]),
  .iBusWishbone_SEL(output_d[68:65]),
  .iBusWishbone_ERR(input_lat[99]),
  .iBusWishbone_CTI(output_d[71:69]),
  .iBusWishbone_BTE(output_d[73:72]),
  .dBusWishbone_CYC(output_d[74]),
  .dBusWishbone_STB(output_d[75]),
  .dBusWishbone_ACK(input_lat[100]),
  .dBusWishbone_WE(output_d[76]),
  .dBusWishbone_ADR(output_d[106:77]),
  .dBusWishbone_DAT_MISO(input_lat[132:101]),
  .dBusWishbone_DAT_MOSI(output_d[138:107]),
  .dBusWishbone_SEL(output_d[142:139]),
  .dBusWishbone_ERR(input_lat[133]),
  .dBusWishbone_CTI(output_d[145:143]),
  .dBusWishbone_BTE(output_d[147:146]),
  .clk(clk),
  .reset(reset)
);




endmodule
