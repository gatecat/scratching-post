from soc import Ulx3sSoc
from sim.platform import SimPlatform

if __name__ == '__main__':
    platform = SimPlatform()
    platform.build(Ulx3sSoc())
