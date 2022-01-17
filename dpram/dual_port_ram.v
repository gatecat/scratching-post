`timescale 1ns/1ps

module sequence_gen(input clk, output clkx2, output wr_rdn);

localparam DEL = 20;
wire [DEL:0] delay_line;

assign delay_line[0] = clk;

genvar ii;
for (ii = 0; ii < DEL; ii = ii + 1'b1) begin: bufs
	(* keep *) BUF buf_i (.A(delay_line[ii]), .Q(delay_line[ii + 1]));
end

wire inv_dly_0, inv_dly_1;
wire pulse_0, pulse_1;


(* keep *) INV inv_0 (.A(delay_line[5]), .Q(inv_dly_0));
(* keep *) INV inv_1 (.A(delay_line[20]), .Q(inv_dly_1));

(* keep *) NAND pulse_gen_0 (.A(clk), .B(inv_dly_0), .Q(pulse_0));
(* keep *) NAND pulse_gen_1 (.A(delay_line[15]), .B(inv_dly_1), .Q(pulse_1));

(* keep *) NAND pulse_or (.A(pulse_0), .B(pulse_1), .Q(clkx2));

assign wr_rdn = delay_line[10];

endmodule

module dpram(input clk, input [7:0] waddr, raddr, wdata, input we, output [7:0] rdata);

	wire clkx2;
	wire wr_rdn_seq, rd_wrn_ram;
	wire [7:0] addr_ram;

	sequence_gen seq_i (.clk(clk), .clkx2(clkx2), .wr_rdn(wr_rdn_seq));

	// Enable a write if the sequence generator is in the write phase and write enable is asserted
	NAND wrn_or_i (.A(wr_rdn_seq), .B(we), .Q(rd_wrn_ram));

	// Select between the two addresses
	genvar ii;
	for (ii = 0; ii < 8; ii = ii + 1'b1) begin: addr_muxes
		(* keep *) MUX2 mux_i (.A(waddr[ii]), .B(raddr[ii]), .S(rd_wrn_ram), .Q(addr_ram[ii]));
	end

	RAM_BLOCK ram_i(.CLK(clkx2), .ADDR(addr_ram), .WDATA(wdata), .RD_WRN(rd_wrn_ram), .RDATA(rdata));

endmodule


module testbench;
	reg clk;
	always #20 clk = (clk === 1'b0);

	reg [7:0] waddr, wdata, raddr;
	reg we;
	wire [7:0] rdata;

	initial begin
		$dumpfile("dual_port_ram.vcd");
		$dumpvars(0, testbench);
		// Init
		we = 1'b0;
		raddr = 8'h00;
		waddr = 8'h00;
		raddr = 8'h00;
		repeat (1) @(posedge clk);
		repeat (1) @(negedge clk);
		// Write some test values
		we = 1'b1;
		waddr = 8'h00;
		wdata = 8'h55;
		repeat (1) @(negedge clk);
		waddr = 8'h01;
		wdata = 8'hAA;
		repeat (1) @(negedge clk);
		// Test read and write
		waddr = 8'h02;
		raddr = 8'h01;
		wdata = 8'h5A;
		repeat (1) @(negedge clk)
		// Test read only
		raddr = 8'h02;
		we = 1'b0;
		$display("rdata %x (expected aa)", rdata);
		repeat (1) @(negedge clk)
		$display("rdata %x (expected 5a)", rdata);
		$finish;
	end

	dpram dut(.clk(clk), .waddr(waddr), .raddr(raddr), .wdata(wdata), .we(we), .rdata(rdata));

endmodule
