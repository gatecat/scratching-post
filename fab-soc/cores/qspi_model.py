class QspiModel:
    def __init__(self, cs_width=3, num_flash=1, num_rams=3,
        flash_size=2**20, ram_size=2**20,
        encoded_cs=True,
        verbose=True):
        self.num_flash = num_flash
        self.num_rams = num_rams
        self.verbose = verbose
        self.xfer_count = 0

        self._cs_width = cs_width
        self._encoded_cs = encoded_cs
        self._last_sclk = False
        self._last_csn = (1 << cs_width) - 1
        self._bit_count = 0
        self._byte_count = 0
        self._data_width = 0
        self._addr = 0
        self._curr_byte = 0
        self._command = 0
        self._out_buffer = 0
        self._data_in = 0
        self._data_out = 0

        self.data = []
        for i in range(num_flash):
            self.data.append(bytearray(flash_size))
        for i in range(num_rams):
            self.data.append(bytearray(ram_size))

        self._flash_id = [0xEF, 0x40, 0x18, 0xFF]
        self._ram_id = [0x0D, 0x5D, 0x40, 0xFF]

    def log(self, s):
        if self.verbose:
            print(s)

    def _get_dev(self, cs):
        cs_mask = (1 << self._cs_width) - 1
        if cs == cs_mask:
            return -1
        elif self._encoded_cs:
            return cs
        else:
            for i in range(self.num_rams+self.num_flash):
                if cs == (~(1 << i)) & cs_mask:
                    return i
            assert False, f"{cs:0b}"

    def reset(self):
        self._bit_count = 0
        self._byte_count = 0
        self._data_width = 1

    def process_byte(self, dev):
        is_ram = dev >= self.num_flash
        if self._byte_count == 0:
            self._addr = 0
            self._data_width = 1
            # command byte
            self._command = self._curr_byte
            self.log(f"SPI command: {self._command:02x}")
            if self._command == 0xab:
                pass # power up
            elif self._command in (0x0b, 0x02, 0x9f):
                # SPI fast read, SPI write, read ID
                pass
            elif self._command in (0xeb, 0x38):
                # quad read, quad write
                self._data_width = 4
            else:
                self.log(f"  unknown command!")
            self.xfer_count += 1
        else:
            if self._command == 0x0b:
                # SPI fast read
                if self._byte_count <= 3:
                    self._addr |= (self._curr_byte) << ((3 - self._byte_count) * 8)
                elif self._byte_count >= 4: # 8 dummy bits
                    if self._byte_count == 4:
                        self.log(f"   begin SPI read at {self._addr:06x}")
                    self._out_buffer = self.data[dev][self._addr % len(self.data[dev])]
                    self._addr = (self._addr + 1) & 0x00FFFFFF
            elif self._command == 0xeb:
                # quad read
                dummy_mode = 3
                if self._byte_count <= 3:
                    self._addr |= (self._curr_byte) << ((3 - self._byte_count) * 8)
                elif self._byte_count == 4 and not is_ram:
                    # one mode byte
                    pass
                elif self._byte_count >= (3+dummy_mode): # addr, mode and dummy bits
                    if self._byte_count == (3+dummy_mode):
                        self.log(f"   begin quad read at {self._addr:06x}")
                    self._out_buffer = self.data[dev][self._addr % len(self.data[dev])]
                    self._addr = (self._addr + 1) & 0x00FFFFFF
            elif self._command in (0x02, 0x38):
                if self._byte_count <= 3:
                    self._addr |= (self._curr_byte) << ((3 - self._byte_count) * 8)
                else:
                    if self._byte_count == 4:
                        self.log(f"   begin SPI write at {self._addr:06x}")
                    self.data[dev][self._addr % len(self.data[dev])] = self._curr_byte
                    self._addr = (self._addr + 1) & 0x00FFFFFF
            elif self._command == 0x9f:
                data = self._ram_id if is_ram else self._flash_id
                self._out_buffer = data[self._curr_byte % len(data)]

    def posedge(self, dev):
        if self._data_width == 4:
            self._curr_byte = ((self._curr_byte << 4) | (self._data_in & 0xF) ) & 0xFF
        else:
            self._curr_byte = ((self._curr_byte << 1) | (self._data_in & 0x1) ) & 0xFF
        self._out_buffer = (self._out_buffer << self._data_width) & 0xFF
        self._bit_count += self._data_width
        if self._bit_count == 8:
            self.process_byte(dev)
            self._byte_count += 1
            self._bit_count = 0

    def negedge(self, dev):
        if self._data_width == 4:
            self._data_out = (self._out_buffer >> 4) & 0xF
        else:
            self._data_out = ((self._out_buffer >> 7) & 0x1) << 1

    def tick(self, sclk, csn, din):
        self._data_in = din
        if csn != self._last_csn:
            self.reset()
        dev = self._get_dev(csn)
        if dev != -1 and sclk and not self._last_sclk:
            self.posedge(dev)
        if dev != -1 and not sclk and self._last_sclk:
            self.negedge(dev)
        self._last_sclk = sclk
        self._last_csn = csn
        return self._data_out
