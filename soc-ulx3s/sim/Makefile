CXXFLAGS=-O3 -g -std=c++17
RTL_CXXFLGAGS=-O1 -std=c++17

all: build/sim_soc

build/sim_soc.ys: ../sim_soc.py $(wildcard cores/*.py)
	(cd .. && python -m sim_soc)

build/sim_soc.cc: build/sim_soc.ys
	(cd build && yosys sim_soc.ys)

build/sim_soc.h: build/sim_soc.cc

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

run: build/sim_soc
	./build/sim_soc

.PRECIOUS: build/sim_soc.ys build/sim_soc.cc
.PHONY: run
