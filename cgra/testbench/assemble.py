_bits = 32

def _parse_features(filename):
    result = dict()
    with open(filename, "r") as f:
        for line in f:
            sl = line.strip().split(" ")
            if len(sl) == 0:
                continue
            result[sl[0]] = [int(x) for x in sl[1:]]
    return result

def _parse_config(filename):
    result = []
    with open(filename, "r") as f:
        for line in f:
            sl = line.strip()
            if '#' in sl:
                sl = sl.split('#', 2)[0].strip()
            result.append(sl)
    return result

def _gen_bitmap(features, config):
    total_bits = max(max(v) for v in features.values() if len(v) > 0)
    total_frames = (total_bits + _bits - 1) // _bits
    bitmap = [0 for i in range(total_frames)]
    for cfg in config:
        assert cfg in features, f"unknown config {cfg}"
        for bit in features[cfg]:
            bitmap[bit // _bits] |= (1 << (bit % _bits))
    return bitmap

def _write_bitmap(bitmap, file):
    with open(file, "w") as f:
        for line in bitmap:
            print(f"{line:0{_bits}b}", file=f)

def main():
    import sys
    if len(sys.argv) != 4:
        print("Usage: assemble.py <features> <config> <bitmap>")
        sys.exit(1)
    bitmap = _gen_bitmap(_parse_features(sys.argv[1]), _parse_config(sys.argv[2]))
    _write_bitmap(bitmap, sys.argv[3])

if __name__ == '__main__':
    main()
