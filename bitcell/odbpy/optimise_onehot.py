# Copyright 2021-2022 Efabless Corporation
# Copyright 2022 gatecat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import odb

import os
import sys
import inspect
import functools
import math
from random import Random

import click

class OdbReader(object):
    def __init__(self, *args):
        self.db = odb.dbDatabase.create()
        if len(args) == 1:
            db_in = args[0]
            self.db = odb.read_db(self.db, db_in)
        elif len(args) == 2:
            lef_in, def_in = args
            if not (isinstance(lef_in, list) or isinstance(lef_in, tuple)):
                lef_in = [lef_in]
            for lef in lef_in:
                odb.read_lef(self.db, lef)
            if def_in is not None:
                odb.read_def(self.db, def_in)

        self.tech = self.db.getTech()
        self.chip = self.db.getChip()
        if self.chip is not None:
            self.block = self.db.getChip().getBlock()
            self.name = self.block.getName()
            self.rows = self.block.getRows()
            self.dbunits = self.block.getDefUnits()
            self.instances = self.block.getInsts()

    def add_lef(self, new_lef):
        odb.read_lef(self.db, new_lef)

def click_odb(function):
    @functools.wraps(function)
    def wrapper(input_db, output, output_def, input_lef, **kwargs):
        reader = OdbReader(input_db)

        signature = inspect.signature(function)
        parameter_keys = signature.parameters.keys()

        kwargs = kwargs.copy()
        kwargs["reader"] = reader

        if "input_db" in parameter_keys:
            kwargs["input_db"] = input_db
        if "input_lef" in parameter_keys:
            kwargs["input_lef"] = input_lef
        if "output" in parameter_keys:
            kwargs["output"] = output

        if input_db.endswith(".def"):
            print(
                "Error: Invocation was not updated to use an odb file.", file=sys.stderr
            )
            exit(os.EX_USAGE)

        function(**kwargs)

        if output_def is not None:
            odb.write_def(reader.block, output_def)
        odb.write_db(reader.db, output)

    wrapper = click.option(
        "-O", "--output-def", default="./out.def", help="Output DEF file"
    )(wrapper)
    wrapper = click.option(
        "-o", "--output", default="./out.odb", help="Output ODB file"
    )(wrapper)
    wrapper = click.option(
        "-l",
        "--input-lef",
        required=True,
        help="LEF file needed to have a proper view of the DEF files",
    )(wrapper)
    wrapper = click.argument("input_db")(wrapper)

    return wrapper

@click.command()
@click_odb
def optimise_onehot(reader):
    instances = reader.block.getInsts()
    muxes = []

    bit_to_mux = dict()
    mux_to_bit = dict()
    wordline_signals = dict()
    bitline_signals = dict()

    def get_index(sig):
        b0 = sig.find('\\[')
        b1 = sig.find('\\]')
        return int(sig[b0+2:b1])

    for instance in instances:
        if instance.getMaster().getName() == "sky130_fpga_bitmux":
            muxes.append(instance)
            wla = instance.findITerm("WLA").getNet()
            wlb = instance.findITerm("WLB").getNet()
            blp = instance.findITerm("BLP").getNet()
            bln = instance.findITerm("BLN").getNet()
            assert wla.getName() == wlb.getName(), (wla.getName(), wlb.getName())
            word = get_index(wla.getName())
            bit = get_index(blp.getName())
            wordline_signals[word] = wla
            bitline_signals[bit] = (blp, bln)
            assert (word, bit) not in bit_to_mux
            bit_to_mux[(word, bit)] = instance
            mux_to_bit[instance.getName()] = (word, bit)

    def net_hpwl(net):
        for i, it in enumerate(net.getITerms()):
            found, px, py = it.getAvgXY()
            if not found:
                # Failed, use the center coordinate of the instance as fall back
                px, py = it.getInst().getLocation()
            if i == 0:
                x0 = x1 = px
                y0 = y1 = py
            else:
                x0 = min(x0, px)
                x1 = max(x1, px)
                y0 = min(y0, py)
                y1 = max(y1, py)
        return abs(y1 - y0) + abs(x1 - x0)
    def total_hpwl():
        hpwl = 0
        for wl in wordline_signals.values():#
            hpwl += net_hpwl(wl)
        for blp, bln in bitline_signals.values():#
            hpwl += net_hpwl(blp)
            hpwl += net_hpwl(bln)
        return hpwl

    r  = Random(1)
    temperature = 1
    n_accept = 0
    n_moves = 0
    def move_mux(mux, word, bit):
        for wli in ("WLA", "WLB"):
            wl = mux.findITerm(wli)
            wl.disconnect()
            wl.connect(wordline_signals[word])
        for bli, sig in zip(("BLP", "BLN"), bitline_signals[bit]):
            bl = mux.findITerm(bli)
            bl.disconnect()
            bl.connect(sig)
        bit_to_mux[(word, bit)] = mux
        mux_to_bit[mux.getName()] = (word, bit)

    def anneal_swap(mux, word, bit):
        nonlocal n_moves, n_accept
        n_moves += 1
        old_word, old_bit = mux_to_bit[mux.getName()]
        if word == old_word and bit == old_bit:
            return
        wires = [wordline_signals[word], bitline_signals[bit][0], bitline_signals[bit][1]]
        if word != old_word:
            wires.append(wordline_signals[old_word])
        if bit != old_bit:
            wires += bitline_signals[old_bit]
        # see if position we are swapping to is occupied
        other_mux = bit_to_mux.get((word, bit), None)
        old_hpwl = sum(net_hpwl(w) for w in wires)
        # perform swap and compute new HPWL
        move_mux(mux, word, bit)
        if other_mux:
            move_mux(other_mux, old_word, old_bit)
        else:
            bit_to_mux[(old_word, old_bit)] = None
        new_hpwl = sum(net_hpwl(w) for w in wires)
        delta = new_hpwl - old_hpwl
        if delta < 0 or (temperature > 1e-8 and (r.random() / 2) <= math.exp(-delta/temperature)):
            # accept
            n_accept += 1
        else:
            # revert
            move_mux(mux, old_word, old_bit)
            if other_mux:
                move_mux(other_mux, word, bit)
            else:
                bit_to_mux[(word, bit)] = None


    radius = len(wordline_signals)
    i = 0
    avg_hpwl = total_hpwl()
    while temperature >= 1e-7 and radius > 2:
        print(f"i={i} hpwl={total_hpwl()} T={temperature:.2f} R={radius}")
        for j in range(10):
            for (word, bit), mux in r.sample(list(bit_to_mux.items()), k=len(bit_to_mux)):
                if mux is None:
                    continue
                new_word = word + r.randint(-radius, radius)
                new_bit = bit + r.randint(-radius, radius)
                if new_word < 0 or new_word >= len(wordline_signals) or new_bit < 0 or new_bit >= len(bitline_signals):
                    # oob
                    continue
                anneal_swap(mux, new_word, new_bit)
        r_accept = n_accept / n_moves
        curr_hpwl = total_hpwl()
        if curr_hpwl < (0.95 * avg_hpwl):
            avg_hpwl = 0.8 * avg_hpwl + 0.2 * curr_hpwl
        else:
            radius = max(1, min(len(wordline_signals)//2, int(radius * (1.0 - 0.44 + r_accept) + 0.5)))
            if r_accept > 0.96: temperature *= 0.5
            elif r_accept > 0.8: temperature *= 0.9
            elif r_accept > 0.15 and radius > 1: temperature *= 0.95
            else: temperature *= 0.8
        n_accept = 0
        n_moves = 0
        i += 1


if __name__ == "__main__":
    optimise_onehot()

