module pic10(input clock, reset, output reg [3:0] prog_adr, input [11:0] prog_data, input [3:0] gpi, output reg [7:0] gpo);
	wire [7:0] reg_rdata;
	reg [7:0] result;
	reg [7:0] w;
	reg [1:0] phase;
	reg [3:0] next_pc;
	reg next_skip;
	reg reg_we;
	reg w_we;

	always @(posedge clock, negedge reset)
	begin
		if (!reset) begin
			phase <= 2'b0;
		end else begin
			phase <= phase + 1'b1;
		end
	end

	always @(posedge clock, negedge reset)
	begin
		if (!reset) begin
			pc <= 1'b0;
			next_pc <= 1'b0;
			w <= 1'b0;
			next_skip <= 1'b0;
		end else begin
			if (phase == 0) begin
				skip <= next_skip;
				next_skip <= 1'b0;
				reg_we <= 1'b0;
				w_we <= 1'b0;
				pc <= next_pc;
			end else if (phase == 1) begin
				next_pc <= prog_adr + 1'b1;
				if (prog_data[11:10] == 2'b00) begin
					reg_we <= prog_data[5] & (prog_data[9:6] != 4'b0000);
					w_we <= ~prog_data[5] & (prog_data[9:6] != 4'b0000);
					case (prog_data[9:6])
						4'b0001: result <= 0;
						4'b0010: result <= reg_rdata - w;
						4'b0011: result <= reg_rdata - 1;
						4'b0100: result <= reg_rdata | w;
						4'b0101: result <= reg_rdata & w;
						4'b0111: result <= reg_rdata + w;
						4'b1000: result <= reg_rdata;
						4'b1001: result <= ~reg_rdata;
						4'b1010: result <= reg_rdata + 1;
						4'b1010: begin result <= reg_rdata - 1; next_skip <= reg_rdata == 8'h01; end
						4'b1111: begin result <= reg_rdata + 1; next_skip <= reg_rdata == 8'hff; end
					endcase
				end else if (prog_data[11:10] == 2'b01) begin
					case (prog_data[9:8])
						2'b00: result <= reg_rdata & ~(1 << prog_data[7:5]);
						2'b01: result <= reg_rdata | (1 << prog_data[7:5]);
						2'b10: begin result <= reg_rdata; next_skip <= ~reg_rdata[prog_data[7:5]]; end
						2'b11: begin result <= reg_rdata; next_skip <= reg_rdata[prog_data[7:5]]; end
					endcase
				end else if (prog_data[11:10] == 2'b10) begin
					// no call, return
					if (prog_data[9] == 1'b1)
						next_pc <= prog_data[3:0];
				end else if (prog_data[11:10] == 2'b11) begin
					w_we <= 1'b1;
					case (prog_data[9:8])
						2'b00: result <= prog_data[7:0];
						2'b01: result <= prog_data[7:0] | w;
						2'b10: result <= prog_data[7:0] & w;
						2'b11: result <= prog_data[7:0] ^ w;
					endcase
				end
			end else if (phase == 2) begin
				if (!skip) begin
					if (w_we)
						w <= result;
				end
			end else if (phase == 3) begin
				// ...
			end
		end
	end

	wire [4:0] reg_addr = prog_data[4:0];
	always @(posedge clock) begin
		if (reg_we && (phase == 2) && reg_addr[4] && !skip)
			gpo <= result;
	end

	wire [7:0] reg_rdata;
	wire [7:0] regf_data[0:3];
	assign reg_rdata = reg_addr[4] ? {4'b0000, gpi} : regf_data[reg_addr[1:0]];

	// register file
	wire regf_we = phase[1] & reg_we & !skip;

	generate
		genvar ii, jj;
		for (ii = 0; ii < 4; ii = ii + 1'b1) begin:word
			for (jj = 0; jj < 8; jj = jj + 1'b1) begin:bits
				sky130_fd_sc_hd__dlrtp_1 rfbit_i (
					.GATE(regf_we && (reg_addr[1:0] == ii)),
					.RESET_B(reset),
					.D(result[jj]),
					.Q(regf_data[ii][jj])
				);
			end
		end
	endgenerate

endmodule

(* blackbox *)
module sky130_fd_sc_hd__dlrtp_1(input GATE, RESET_B, D, output reg Q);
	always @*
		if (~RESET_B)
			Q <= 0;
		else if (GATE)
			Q <= D;
endmodule

(* blackbox *)
module sky130_fd_sc_hd__dlxtp_1(input GATE, D, output reg Q);
	always @*
		if (GATE)
			Q <= D;
endmodule

// serially loaded program memory
module pic_progmem(input write_phi0, write_phi1, write_data, write_enable, input [3:0] adr, output [11:0] prog_data);
	localparam K = 8;
	wire [12*K-1:0] bits;
	generate
		genvar ii;
		for (ii = 0; ii < 12*K; ii = ii + 1'b1) begin
			sky130_fd_sc_hd__dlxtp_1 progbit_i (
				.GATE(ii[0] ? write_phi1 : write_phi0),
				.D((ii == 0) ? write_data : bits[ii-1]),
				.Q(bits[ii])
			);
		end
	endgenerate
	assign prog_data = bits[adr*12 +: 12];
endmodule

