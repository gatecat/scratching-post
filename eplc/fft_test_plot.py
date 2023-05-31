import math
from math import pi
import matplotlib.pyplot as plt
import numpy as np
from scipy import fft

import sys

def parse_csv(filename):
	result = []
	with open(filename, "r") as f:
		for line in f:
			sl = line.strip().split(",")
			if len(sl) == 0:
				continue
			result.append([float(x) for x in sl if x != ""])
	return result

density = parse_csv(sys.argv[1])
assert "out_bin_density_" in sys.argv[1]
potential = parse_csv(sys.argv[1].replace("out_bin_density_", "out_bin_phi_prefft_"))
x_field = parse_csv(sys.argv[1].replace("out_bin_density_", "out_bin_ex_"))
y_field = parse_csv(sys.argv[1].replace("out_bin_density_", "out_bin_ey_"))

fig, axs = plt.subplots(2, 2)
axs[0,0].imshow(density, cmap='hot', interpolation='nearest')
axs[0,0].set_title("density")

axs[0,1].imshow(potential, cmap='coolwarm', interpolation='nearest')
axs[0,1].set_title("potential")

axs[1,0].imshow(x_field, cmap='coolwarm', interpolation='nearest')
axs[1,0].set_title("field X component")

axs[1,1].imshow(y_field, cmap='coolwarm', interpolation='nearest')
axs[1,1].set_title("field Y component")

plt.show()