import math
from math import pi
import matplotlib.pyplot as plt
import numpy as np
from scipy import fft

import sys

in_density = []

with open(sys.argv[1], "r") as f:
	for line in f:
		sl = line.strip().split(",")
		if len(sl) == 0:
			continue
		in_density.append([float(x) for x in sl if x != ""])

width = len(in_density[0])
height = len(in_density)

m = 64

xs = (m / width)
ys = (m / height)

density = np.array([[0] * m] * m)
for y, row in enumerate(in_density):
	for x, d in enumerate(row):
		x0 = int(x * xs)
		x1 = min(x0 + 1, m-1)
		y0 = int(y * ys)
		y1 = min(y0 + 1, m-1)
		# stamp across density bins
		density[y0,x0] += d * (x - x0/xs)*xs * (y - y0/ys)*ys
		density[y1,x0] += d * (x - x0/xs)*xs * (y1/ys - y)*ys
		density[y0,x1] += d * (x1/xs - x)*xs * (y - y0/ys)*ys
		density[y1,x1] += d * (x1/xs - x)*xs * (y1/ys - y)*ys

a = fft.dctn(density, type=1)
for v in range(m):
	for u in range(m):
		# differing scale factors
		a[v, u] *= (2 / m**2)

potential = np.array([[0] * m] * m)
for v in range(m):
	for u in range(m):
		w_u = (2*pi*u)/m
		w_v = (2*pi*v)/m
		if v != 0 or u != 0:
			potential[v,u] = a[v,u] * (1.0 / (w_u**2 + w_v**2))

potential = fft.dctn(potential, type=1)

fig, axs = plt.subplots(2, 2)
axs[0,0].imshow(density, cmap='hot', interpolation='nearest')
axs[0,0].set_title("density")

axs[0,1].imshow(potential, cmap='coolwarm', interpolation='nearest')
axs[0,1].set_title("potential")

x_field = np.array([[0] * m] * m)
y_field = np.array([[0] * m] * m)
for v in range(m):
	for u in range(m):
		w_u = (2*pi*u)/m
		w_v = (2*pi*v)/m
		if v != 0 or u != 0:
			x_field[v,u] = a[v,u] * (w_u / (w_u**2 + w_v**2))
			y_field[v,u] = a[v,u] * (w_v / (w_u**2 + w_v**2))

# dcst
x_field = fft.dst(x_field, axis=0, type=1)
x_field = fft.dct(x_field, axis=1, type=1)

axs[1,0].imshow(x_field, cmap='coolwarm', interpolation='nearest')
axs[1,0].set_title("field X component")

# dsct
y_field = fft.dct(y_field, axis=0, type=1)
y_field = fft.dst(y_field, axis=1, type=1)

axs[1,1].imshow(y_field, cmap='coolwarm', interpolation='nearest')
axs[1,1].set_title("field Y component")

plt.show()