class QspiModel:
    def __init__(self, cs_width=3, num_flash=1, num_rams=1,
        flash_size=2**20, ram_size=2**20,
        encoded_cs=True):
        self.num_flash = num_flash
        self.num_rams = num_rams
        self._encoded_cs = encoded_cs
        self._last_sclk = False
        self._last_cs = (1 << cs_width) - 1
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
            data.append(bytearray(flash_size))
        for i in range(num_rams):
            data.append(bytearray(ram_size))

    def _get_dev(self, cs):
        cs_mask = (1 << cs_width) - 1
        if cs == cs_mask:
            return -1
        elif self.encoded_cs:
            return cs
        else:
            for i in range(num_rams+num_flash):
                if cs == (~(1 << i)) & cs_mask:
                    return i
            assert False, f"{cs:0b}"

    def reset(self):
        self._bit_count = 0
        self._byte_count = 0
        self._data_width = 1

    def process_byte(self, dev):
        pass

    def posedge(self, dev):
        if self._data_width == 4:
            self._curr_byte = ((self._curr_byte << 4) | (self._data_in & 0xF) ) & 0xFF
        else:
            self._curr_byte = ((self._curr_byte << 1) | (self._data_in & 0x1) ) & 0xFF
        self._out_buffer = (self._out_buffer << self._data_width) & 0xFF
        self._bit_count += self._data_width
        if self._bit_count == 8:
            self.process_byte(dev)
            self._bit_count = 0

    def negedge(self, dev):
        if self._data_width == 4:
            self._data_out = (self._out_buffer >> 4) & 0xF
        else:
            self._data_out = ((self._out_buffer >> 7) & 0x1) << 1

    def tick(self, sclk, csn, din):
        self._data_in = din
        if csn != _last_cs:
            self.reset()
        dev = self._get_dev(csn)
        if dev != -1 and sclk and not self._last_sclk:
            self.posedge(dev)
        if dev != -1 and not sclk and self._last_sclk:
            self.negedge(dev)
        self._last_sclk = sclk
        self._last_cs = cs
        return self._data_out
