import sys

def main():
    with open(sys.argv[1], "r") as li:
        with open(sys.argv[2], "w") as lo:
            curr_pin = None
            for line in li:
                if "CLASS BLOCK" in line:
                    print("  CLASS core ;", file=lo)
                else:
                    print(line[:-1], file=lo)
                    if "ORIGIN" in line:
                        print("  SYMMETRY X Y ;", file=lo)
                        print("  SITE unithd ;", file=lo)
                    if "USE POWER" in line or "USE GROUND" in line:
                        print("     SHAPE ABUTMENT ;", file=lo)
if __name__ == '__main__':
    main()
