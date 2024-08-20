all: tap_demo

CXXFLAGS = -I$(shell yosys-config --datdir)/include/backends/cxxrtl/runtime -O3 -g
CFLAGS = -Itapcfg/src/include

tapcfg:
	git clone https://github.com/enjoy-digital/tapcfg

tap_demo.il: tap_demo.py
	pdm run python -m tap_demo generate tap_demo.il

tap_demo.cc: tap_demo.il
	yosys -p "hierarchy -top top; write_cxxrtl tap_demo.cc" tap_demo.il

tapcfg/src/lib/tapcfg.c: tapcfg

tapcfg.o: tapcfg/src/lib/tapcfg.c
	$(CC) $(CFLAGS) -c -o $@ $<

taplog.o: tapcfg/src/lib/taplog.c
	$(CC) $(CFLAGS) -c -o $@ $<

main.o: main.cc tap_demo.cc
	$(CXX) $(CXXFLAGS) -c -o $@ $<

tap_demo: tapcfg.o taplog.o main.o
	$(CXX) $(LDFLAGS) -o $@ $^
