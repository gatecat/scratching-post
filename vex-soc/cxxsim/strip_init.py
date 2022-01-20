import sys
stripped = ""
with open(sys.argv[1], "r") as f:
	in_meminit = False
	for line in f:
		if "cell $meminit" in line:
			in_meminit = True
		if in_meminit:
			if "end" in line:
				in_meminit = False
		else:
			stripped += line
with open(sys.argv[1], "w") as f:
	f.write(stripped)

