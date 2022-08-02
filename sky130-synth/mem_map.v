module $__SKY130_32X256 (...);

input PORT_A_CLK;
input [7:0] PORT_A_ADDR;
input PORT_A_WR_EN;
input [3:0] PORT_A_WR_BE;
input [31:0] PORT_A_WR_DATA;
output [31:0] PORT_A_RD_DATA;

input PORT_B_CLK;
input [7:0] PORT_B_ADDR;
output [31:0] PORT_B_RD_DATA;

sky130_sram_1kbyte_1rw1r_32x256_8 _TECHMAP_REPLACE_ (
	.clk0(PORT_A_CLK), .csb0(1'b1),
	.web0(~PORT_A_WR_EN), .wmask0(PORT_A_WR_BE),
	.addr0(PORT_A_ADDR),
	.din0(PORT_A_WR_DATA), .dout0(PORT_A_RD_DATA),

	.clk1(PORT_B_CLK), .csb1(1'b1),
	.addr1(PORT_B_ADDR),
	.dout1(PORT_B_RD_DATA)
);

endmodule

module $__SKY130_8X1024 (...);

input PORT_A_CLK;
input [9:0] PORT_A_ADDR;
input PORT_A_WR_EN;
input [7:0] PORT_A_WR_DATA;
output [7:0] PORT_A_RD_DATA;

input PORT_B_CLK;
input [9:0] PORT_B_ADDR;
output [7:0] PORT_B_RD_DATA;

sky130_sram_1kbyte_1rw1r_8x1024_8 _TECHMAP_REPLACE_ (
	.clk0(PORT_A_CLK), .csb0(1'b1),
	.web0(~PORT_A_WR_EN), .wmask0(1'b1),
	.addr0(PORT_A_ADDR),
	.din0(PORT_A_WR_DATA), .dout0(PORT_A_RD_DATA),

	.clk1(PORT_B_CLK), .csb1(1'b1),
	.addr1(PORT_B_ADDR),
	.dout1(PORT_B_RD_DATA)
);

endmodule
