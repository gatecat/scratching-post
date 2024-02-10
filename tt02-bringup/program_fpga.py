import re
from pyftdi.ftdi import Ftdi
from pyftdi.gpio import GpioAsyncController
import time

OPTIONS_MAP = {
    ("I0", "0"): 0b00 << 0,
    ("I0", "T"): 0b01 << 0,
    ("I0", "R"): 0b10 << 0,
    ("I0", "L"): 0b11 << 0,

    ("I1", "1"): 0b00 << 2,
    ("I1", "~L"): 0b01 << 2,
    ("I1", "B"): 0b10 << 2,
    ("I1", "R"): 0b11 << 2,

    ("S", "0"):  0b100 << 4,
    ("S", "1"):  0b000 << 4,
    ("S", "T"):  0b101 << 4,
    ("S", "~T"): 0b001 << 4,
    ("S", "R"):  0b110 << 4,
    ("S", "~R"): 0b010 << 4,
    ("S", "L"):  0b111 << 4,
    ("S", "~L"): 0b011 << 4,

    ("Q", "MUX"): 0b0 << 7,
    ("Q", "DFF"): 0b1 << 7,
}

WIDTH = 5
HEIGHT = 6

def assemble_chip(config):
    tile_config = [[0 for i in range(WIDTH)] for i in range(HEIGHT)]
    for entry in config:
        sl = entry.strip().split("#", 2)[0]
        if len(sl) == 0:
            continue
        spl = sl.split(".")
        assert len(spl) == 3, f"bad config line '{entry}'"
        m = re.match(r'Y(\d+)X(\d+)', spl[0])
        x = int(m.group(2))
        y = int(m.group(1))
        tile_config[y][x] |= OPTIONS_MAP[tuple(spl[1:])]
    chip_config = [0 for i in range(HEIGHT * 2)]
    for y, row in enumerate(tile_config):
        for x, tile in enumerate(row):
            for dy in range(2):
                chip_config[y * 2 + dy] |= ((tile >> (4 * dy)) & 0xF) << (x * 4)
    return chip_config

# ORANGE - IN[0] - CFG_DATACLK
# YELLOW - IN[1] - CFG_FRAMEINC
# GREEN  - IN[2] - CFG_FRAMESTRB
# BROWN  - IN[3] - CFG_MODE
# GREY   - IN[4] - CFG_DATA

def main():
    import sys
    with open(sys.argv[1], "r") as f:
        lines = [x.strip() for x in f]
    chip_config = assemble_chip(lines)
    gpio = GpioAsyncController()
    gpio.open_from_url("ftdi:///1", direction=0b11111)
    print("Programming......")
    gpio.write(0b01000) # enter config mode
    time.sleep(1e-3)
    for row in chip_config:
        print(row)
        for i in range(WIDTH * 4):
            gpio.write(0b01000 | (((row >> i) & 0x1) << 4)) # set data bit
            time.sleep(1e-3)
            gpio.write(0b01001 | (((row >> i) & 0x1) << 4)) # clock data bit
            time.sleep(1e-3)
        gpio.write(0b01100) # strobe frame
        time.sleep(1e-3)
        gpio.write(0b01000)
        time.sleep(1e-3)
        gpio.write(0b01010) # increment frame
        time.sleep(1e-3)
        gpio.write(0b01000)
        time.sleep(1e-3)
    gpio.write(0b00000) # exit config mode
    print("Done!")
    print("Clocking user design, ctrl+c to exit")
    while True:
        try:
             gpio.write(0b00001)
             time.sleep(125e-3)
             gpio.write(0b00000)
             time.sleep(125e-3)
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    main()