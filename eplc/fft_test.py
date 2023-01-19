import math
# test density matrix

rho = [
	[1, 0, 2, 0, 0, 0, 0, 1],
	[2, 2, 1, 0, 2, 1, 0, 0],
	[0, 2, 3, 2, 3, 1, 3, 1],
	[2, 4, 4, 3, 4, 3, 2, 2],
	[3, 3, 4, 4, 1, 1, 1, 0],
	[0, 2, 1, 2, 2, 4, 0, 1],
	[1, 2, 1, 1, 2, 1, 2, 2],
	[1, 0, 1, 0, 0, 2, 0, 1],
]

m = 8
w = 2*math.pi/m

# naive approach
result = []
for v in range(m):
	row = []
	for u in range(m):
		a = sum(sum(rho[y][x] * math.cos(w*u*x) * math.cos(w*v*y)
			for x in range(m)) for y in range(m)) / (m**2)
		row.append(a)
	result.append(row)
print(result)
