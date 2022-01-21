CXXFLAGS=-O3 -g -std=c++17
RTL_CXXFLGAGS=-O1 -std=c++17

all: build/sim_soc

clean:
	rm -rf build

cores_py=$(wildcard ../cores/*.py)

build/sim_soc.il: ../soc/sim_soc.py $(cores_py)
	mkdir -p build
	cd .. && python -m soc.sim_soc generate cxxsim/$@
	python strip_init.py $@

build/sim_blackboxes.v: build/sim_soc.il

build/sim_soc.o: build/sim_soc.cc build/sim_soc.h
	$(CXX) -I . -I $(shell yosys-config --datdir)/include $(RTL_CXXFLGAGS) -o $@ -c $<

build/models/%.o: models/%.cc build/sim_soc.h
	mkdir -p build/models
	$(CXX) -I . -I $(shell yosys-config --datdir)/include $(CXXFLAGS) -o $@ -c $<

build/%.o: %.cc build/sim_soc.h
	$(CXX) -I . -I $(shell yosys-config --datdir)/include $(CXXFLAGS) -o $@ -c $<

models_objs=$(patsubst models/%.cc, build/models/%.o, $(wildcard models/*.cc))

build/sim_soc: build/sim_soc.o $(models_objs)  build/main.o
	$(CXX) -o $@ $^

cores_verilog=$(wildcard ../cores/*.v)
vex_verilog=../verilog_gen/VexRiscvLinuxAsic.v

build/sim_soc.cc: build/sim_soc.il build/sim_blackboxes.v $(cores_verilog) $(vex_verilog)
	yosys -p "write_cxxrtl -g4 -header $@" $^

build/sim_soc.h: build/sim_soc.cc


.PRECIOUS: build/sim_soc.il build/sim_soc.cc build/sim_soc.h
