from ..fabric.tiletype import GridDir, TilePort, SwitchMatrix

# Generate the set of ports for the default switch matrix, more ports can be added if needed
def base_ports():
    return [
        TilePort(dir=GridDir.N, src="N1BEG", dy=-1, dst="N1END", width=4),
        TilePort(dir=GridDir.N, src="N2BEG", dy=-1, dst="N2MID", width=8),
        TilePort(dir=GridDir.N, src="N2BEGb", dy=-1, dst="N2END", width=8),
        TilePort(dir=GridDir.N, src="N4BEG", dy=-4, dst="N4END", width=4),
        TilePort(dir=GridDir.N, src="NN4BEG", dy=-4, dst="NN4END", width=4),

        TilePort(dir=GridDir.E, src="E1BEG", dy=1, dst="E1END", width=4),
        TilePort(dir=GridDir.E, src="E2BEG", dy=1, dst="E2MID", width=8),
        TilePort(dir=GridDir.E, src="E2BEGb", dy=1, dst="E2END", width=8),
        TilePort(dir=GridDir.E, src="EE4BEG", dy=4, dst="EE4END", width=4),
        TilePort(dir=GridDir.E, src="E6BEG", dy=6, dst="E6END", width=2),

        TilePort(dir=GridDir.S, src="S1BEG", dy=1, dst="S1END", width=4),
        TilePort(dir=GridDir.S, src="S2BEG", dy=1, dst="S2MID", width=8),
        TilePort(dir=GridDir.S, src="S2BEGb", dy=1, dst="S2END", width=8),
        TilePort(dir=GridDir.S, src="S4BEG", dy=4, dst="S4END", width=4),
        TilePort(dir=GridDir.S, src="SS4BEG", dy=4, dst="SS4END", width=4),

        TilePort(dir=GridDir.W, src="W1BEG", dy=-1, dst="W1END", width=4),
        TilePort(dir=GridDir.W, src="W2BEG", dy=-1, dst="W2MID", width=8),
        TilePort(dir=GridDir.W, src="W2BEGb", dy=-1, dst="W2END", width=8),
        TilePort(dir=GridDir.W, src="WW4BEG", dy=-4, dst="WW4END", width=4),
        TilePort(dir=GridDir.W, src="W6BEG", dy=-6, dst="W6END", width=2),

        TilePort(dir=GridDir.J, src="J2MID_ABa_BEG", dst="J2MID_ABa_END", width=4),
        TilePort(dir=GridDir.J, src="J2MID_CDa_BEG", dst="J2MID_CDa_END", width=4),
        TilePort(dir=GridDir.J, src="J2MID_EFa_BEG", dst="J2MID_EFa_END", width=4),
        TilePort(dir=GridDir.J, src="J2MID_GHa_BEG", dst="J2MID_GHa_END", width=4),

        TilePort(dir=GridDir.J, src="J2MID_ABb_BEG", dst="J2MID_ABb_END", width=4),
        TilePort(dir=GridDir.J, src="J2MID_CDb_BEG", dst="J2MID_CDb_END", width=4),
        TilePort(dir=GridDir.J, src="J2MID_EFb_BEG", dst="J2MID_EFb_END", width=4),
        TilePort(dir=GridDir.J, src="J2MID_GHb_BEG", dst="J2MID_GHb_END", width=4),

        TilePort(dir=GridDir.J, src="J2END_AB_BEG", dst="J2END_AB_END", width=4),
        TilePort(dir=GridDir.J, src="J2END_CD_BEG", dst="J2END_CD_END", width=4),
        TilePort(dir=GridDir.J, src="J2END_EF_BEG", dst="J2END_EF_END", width=4),
        TilePort(dir=GridDir.J, src="J2END_GH_BEG", dst="J2END_GH_END", width=4),

        TilePort(dir=GridDir.J, src="JN2BEG", dst="JN2END", width=8),
        TilePort(dir=GridDir.J, src="JE2BEG", dst="JE2END", width=8),
        TilePort(dir=GridDir.J, src="JS2BEG", dst="JS2END", width=8),
        TilePort(dir=GridDir.J, src="JW2BEG", dst="JW2END", width=8),

        TilePort(dir=GridDir.J, src="J_l_AB_BEG", dst="J_l_AB_END", width=4),
        TilePort(dir=GridDir.J, src="J_l_CD_BEG", dst="J_l_CD_END", width=4),
        TilePort(dir=GridDir.J, src="J_l_EF_BEG", dst="J_l_EF_END", width=4),
        TilePort(dir=GridDir.J, src="J_l_GH_BEG", dst="J_l_GH_END", width=4),

    ]

# Generate a derivative of the default FABulous switch matrix. Currently this is optimised for a roughly LUT4 arch
# More flexible switch matrix generation based on what it's connecting to is a problem for a future myrtle cat...
def base_switch_matrix(inputs=[], ce_inputs=[], sr_inputs=[], sel_inputs=[], outputs=[], mux_outputs=[]):
    result = SwitchMatrix()
    for base in _base_matrix:
        result.add(base)
    # "LUT" inputs
    for i, inp in enumerate(inputs):
        im = i % 32 # in practice exceeding 32 is gonna be bad
        sl = im // 8 # consider split into 4 SLICEs of 8 inputs each
        j = im % 4 # for a LUT, the LUT input index
        s = ("AB", "CD", "EF", "GH")[sl]
        result.add(inp, [
            f"J2MID_{s}a_END{j}",
            f"J2MID_{s}b_END{j}",
            f"J2END_{s}_END{j}",
            f"J_l_{s}_END{j}",
        ])
    # "MUX" inputs
    for i, inp in enumerate(sel_inputs):
        result.add(inp, [f"J{d}2END{(i + 4) % 8}" for d in "NESW"])
    # output-associated routing
    #   output->double
    if len(outputs) > 0:
        for i in range(8):
            o = [outputs[(8*i + j) % len(outputs)] for j in range(8) if j != i]
            for d in "NESW":
                result.add(f"J{d}2BEG{i}", o)
                # TODO: this does permute them a bit different to the original matrix
                #  does that matter? for future cat
                if len(mux_outputs) > 0:
                    result.add(f"J{d}2BEG{i}", [mux_outputs[i % len(mux_outputs)], ])
        for i in range(4):
            # random permutation attempt
            result.add(f"N1BEG{i}", [outputs[(11+i) % len(outputs)]])
            result.add(f"E1BEG{i}", [outputs[(3+i) % len(outputs)]])
            result.add(f"S1BEG{i}", [outputs[(4+i) % len(outputs)]])
            result.add(f"W1BEG{i}", [outputs[(13+i) % len(outputs)]])

            result.add(f"N4BEG{i}", [outputs[(4+i) % len(outputs)]])
            result.add(f"S4BEG{i}", [outputs[(0+i) % len(outputs)]])

            for d in ("NN", "SS", "EE", "WW"):
                ofs = 8 if d in ("NN", "EE") else 0
                result.add(f"N4BEG{i}", [outputs[(4+i+ofs) % len(outputs)]])
                result.add(f"S4BEG{i}", [outputs[(0+i+ofs) % len(outputs)]])
        for i in range(2):
            result.add(f"E6BEG{i}", [outputs[(8*i + j) % len(outputs)] for j in range(8)])
            result.add(f"W6BEG{i}", [outputs[(8*i + j) % len(outputs)] for j in range(8)])
            if len(mux_outputs) > 0:
                result.add(f"E6BEG{i}", [outputs[(2*i + j) % len(mux_outputs)] for j in range(2)])
                result.add(f"W6BEG{i}", [outputs[(2*i + j) % len(mux_outputs)] for j in range(2)])
    return result

# General hardcoded parts from FABulous example
_base_matrix = [
    # double with MID cascade : [N,E,S,W]2BEG --- [N,E,S,W]2MID -> [N,E,S,W]2BEGb --- [N,E,S,W]2END (just routing)
    "[N|E|S|W]2BEGb[0|1|2|3|4|5|6|7],[N|E|S|W]2MID[0|1|2|3|4|5|6|7]",
    # shared double MID jump wires
    "J2MID_ABa_BEG[0|0|0|0],[JN2END3|N2MID6|S2MID6|W2MID6]",
    "J2MID_ABa_BEG[1|1|1|1],[E2MID2|JE2END3|S2MID2|W2MID2]",
    "J2MID_ABa_BEG[2|2|2|2],[E2MID4|N2MID4|JS2END3|W2MID4]",
    "J2MID_ABa_BEG[3|3|3|3],[E2MID0|N2MID0|S2MID0|JW2END3]",
    "J2MID_CDa_BEG[0|0|0|0],[E2MID6|JN2END4|S2MID6|W2MID6]",
    "J2MID_CDa_BEG[1|1|1|1],[E2MID2|N2MID2|JE2END4|W2MID2]",
    "J2MID_CDa_BEG[2|2|2|2],[E2MID4|N2MID4|S2MID4|JS2END4]",
    "J2MID_CDa_BEG[3|3|3|3],[JW2END4|N2MID0|S2MID0|W2MID0]",
    "J2MID_EFa_BEG[0|0|0|0],[E2MID6|N2MID6|JN2END5|W2MID6]",
    "J2MID_EFa_BEG[1|1|1|1],[E2MID2|N2MID2|S2MID2|JE2END5]",
    "J2MID_EFa_BEG[2|2|2|2],[JS2END5|N2MID4|S2MID4|W2MID4]",
    "J2MID_EFa_BEG[3|3|3|3],[E2MID0|JW2END5|S2MID0|W2MID0]",
    "J2MID_GHa_BEG[0|0|0|0],[E2MID6|N2MID6|S2MID6|JN2END6]",
    "J2MID_GHa_BEG[1|1|1|1],[JE2END6|N2MID2|S2MID2|W2MID2]",
    "J2MID_GHa_BEG[2|2|2|2],[E2MID4|JS2END6|S2MID4|W2MID4]",
    "J2MID_GHa_BEG[3|3|3|3],[E2MID0|N2MID0|JW2END6|W2MID0]",

    "J2MID_ABb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_ABb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_ABb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_ABb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",
    "J2MID_CDb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_CDb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_CDb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_CDb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",
    "J2MID_EFb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_EFb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_EFb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_EFb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",
    "J2MID_GHb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_GHb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_GHb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_GHb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",

    # shared double MID jump wires
    "J2MID_ABa_BEG[0|0|0|0],[JN2END3|N2MID6|S2MID6|W2MID6]",
    "J2MID_ABa_BEG[1|1|1|1],[E2MID2|JE2END3|S2MID2|W2MID2]",
    "J2MID_ABa_BEG[2|2|2|2],[E2MID4|N2MID4|JS2END3|W2MID4]",
    "J2MID_ABa_BEG[3|3|3|3],[E2MID0|N2MID0|S2MID0|JW2END3]",
    "J2MID_CDa_BEG[0|0|0|0],[E2MID6|JN2END4|S2MID6|W2MID6]",
    "J2MID_CDa_BEG[1|1|1|1],[E2MID2|N2MID2|JE2END4|W2MID2]",
    "J2MID_CDa_BEG[2|2|2|2],[E2MID4|N2MID4|S2MID4|JS2END4]",
    "J2MID_CDa_BEG[3|3|3|3],[JW2END4|N2MID0|S2MID0|W2MID0]",
    "J2MID_EFa_BEG[0|0|0|0],[E2MID6|N2MID6|JN2END5|W2MID6]",
    "J2MID_EFa_BEG[1|1|1|1],[E2MID2|N2MID2|S2MID2|JE2END5]",
    "J2MID_EFa_BEG[2|2|2|2],[JS2END5|N2MID4|S2MID4|W2MID4]",
    "J2MID_EFa_BEG[3|3|3|3],[E2MID0|JW2END5|S2MID0|W2MID0]",
    "J2MID_GHa_BEG[0|0|0|0],[E2MID6|N2MID6|S2MID6|JN2END6]",
    "J2MID_GHa_BEG[1|1|1|1],[JE2END6|N2MID2|S2MID2|W2MID2]",
    "J2MID_GHa_BEG[2|2|2|2],[E2MID4|JS2END6|S2MID4|W2MID4]",
    "J2MID_GHa_BEG[3|3|3|3],[E2MID0|N2MID0|JW2END6|W2MID0]",

    "J2MID_ABb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_ABb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_ABb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_ABb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",
    "J2MID_CDb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_CDb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_CDb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_CDb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",
    "J2MID_EFb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_EFb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_EFb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_EFb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",
    "J2MID_GHb_BEG[0|0|0|0],[E2MID7|N2MID7|S2MID7|W2MID7]",
    "J2MID_GHb_BEG[1|1|1|1],[E2MID3|N2MID3|S2MID3|W2MID3]",
    "J2MID_GHb_BEG[2|2|2|2],[E2MID5|N2MID5|S2MID5|W2MID5]",
    "J2MID_GHb_BEG[3|3|3|3],[E2MID1|N2MID1|S2MID1|W2MID1]",
    # connection from the double jump wires (stopovers) to the actual double wires      
    # original connection:                     
    # [N|E|S|W]2BEG[0|1|2|3|4|5|6|7],J[N|E|S|W]2END[0|1|2|3|4|5|6|7]
    # the same but without the west routing/connection
    "[N|E|S]2BEG[0|1|2|3|4|5|6|7],J[N|E|S]2END[0|1|2|3|4|5|6|7]",
    "W2BEG[1|2|5|6],JW2END[1|2|5|6]",
    "W2BEG[0|3|4|7],JW2END[0|3|4|7]",
    # the other wires, "operand routing", get just extended; this is like the routing used for a ReCoBus
    ##W2BEG[0|3|4|7],W2END[0|3|4|7]
    # taken from FABulous but with the output wires removed because those are programmatic
    "JN2BEG[0|0|0|0|0|0|0|0],[E1END3|N2END1|E2END1|SS4END1|W2END1|W6END1|E6END1|N4END1]",
    "JN2BEG[1|1|1|1|1|1|1|1],[E1END0|N2END2|E2END2|S2END2|W2END2|W6END0|E6END0|N4END2]",
    "JN2BEG[2|2|2|2|2|2|2|2],[E1END1|N2END3|E2END3|S2END3|W2END3|WW4END1|E6END1|N4END3]",
    "JN2BEG[3|3|3|3|3|3|3|3],[E1END2|N2END4|E2END4|S2END4|W2END4|W6END0|E6END0|N4END0]",
    "JN2BEG[4|4|4|4|4|4|4|4],[W1END3|N2END5|E2END5|S2END5|N1END1|E1END1|S1END1|W1END1]",
    "JN2BEG[5|5|5|5|5|5|5|5],[W1END0|N2END6|E2END6|S2END6|N1END2|E1END2|S1END2|W1END2]",
    "JN2BEG[6|6|6|6|6|6|6|6],[W1END1|N2END7|E2END7|S2END7|N1END3|E1END3|S1END3|W1END3]",
    "JN2BEG[7|7|7|7|7|7|7|7],[W1END2|N2END0|EE4END0|S2END0|N1END0|E1END0|S1END0|W1END0]",

    "JE2BEG[0|0|0|0|0|0|0|0],[N1END3|N2END1|EE4END1|S2END1|W2END1|W6END1|E6END1|N4END1]",
    "JE2BEG[1|1|1|1|1|1|1|1],[N1END0|N2END2|E2END2|S2END2|W2END2|WW4END3|E6END0|N4END2]",
    "JE2BEG[2|2|2|2|2|2|2|2],[N1END1|N2END3|E2END3|S2END3|W2END3|W6END1|E6END1|N4END3]",
    "JE2BEG[3|3|3|3|3|3|3|3],[N1END2|N2END4|E2END4|S2END4|W2END4|W6END0|E6END0|N4END0]",
    "JE2BEG[4|4|4|4|4|4|4|4],[S1END3|N2END5|E2END5|S2END5|N1END1|E1END1|S1END1|W1END1]",
    "JE2BEG[5|5|5|5|5|5|5|5],[S1END0|N2END6|E2END6|S2END6|N1END2|E1END2|S1END2|W1END2]",
    "JE2BEG[6|6|6|6|6|6|6|6],[S1END1|N2END7|E2END7|S2END7|N1END3|E1END3|S1END3|W1END3]",
    "JE2BEG[7|7|7|7|7|7|7|7],[S1END2|N2END0|E2END0|SS4END0|N1END0|E1END0|S1END0|WW4END0]",
                               
    "JS2BEG[0|0|0|0|0|0|0|0],[E1END3|NN4END1|E2END1|S2END1|W2END1|W6END1|E6END1|S4END1]",
    "JS2BEG[1|1|1|1|1|1|1|1],[E1END0|NN4END2|EE4END2|SS4END2|W2END2|W6END0|E6END0|S4END2]",
    "JS2BEG[2|2|2|2|2|2|2|2],[E1END1|NN4END3|E2END3|S2END3|W2END3|W6END1|E6END1|S4END3]",
    "JS2BEG[3|3|3|3|3|3|3|3],[E1END2|N2END4|E2END4|S2END4|W2END4|WW4END2|E6END0|S4END0]",
    "JS2BEG[4|4|4|4|4|4|4|4],[W1END3|N2END5|E2END5|S2END5|N1END1|E1END1|S1END1|W1END1]",
    "JS2BEG[5|5|5|5|5|5|5|5],[W1END0|N2END6|E2END6|S2END6|N1END2|E1END2|S1END2|W1END2]",
    "JS2BEG[6|6|6|6|6|6|6|6],[W1END1|N2END7|E2END7|S2END7|N1END3|E1END3|S1END3|W1END3]",
    "JS2BEG[7|7|7|7|7|7|7|7],[W1END2|N2END0|E2END0|S2END0|N1END0|E1END0|S1END0|W1END0]",
   
    "JW2BEG[0|0|0|0|0|0|0|0],[N1END3|N2END1|E2END1|S2END1|W2END1|W6END1|E6END1|S4END1]",
    "JW2BEG[1|1|1|1|1|1|1|1],[N1END0|N2END2|E2END2|S2END2|W2END2|W6END0|E6END0|S4END2]",
    "JW2BEG[2|2|2|2|2|2|2|2],[N1END1|N2END3|EE4END3|SS4END3|W2END3|W6END1|E6END1|S4END3]",
    "JW2BEG[3|3|3|3|3|3|3|3],[N1END2|N2END4|E2END4|S2END4|W2END4|WW4END2|E6END0|S4END0]",
    "JW2BEG[4|4|4|4|4|4|4|4],[S1END3|N2END5|E2END5|S2END5|N1END1|E1END1|S1END1|W1END1]",
    "JW2BEG[5|5|5|5|5|5|5|5],[S1END0|N2END6|E2END6|S2END6|N1END2|E1END2|S1END2|W1END2]",
    "JW2BEG[6|6|6|6|6|6|6|6],[S1END1|N2END7|E2END7|S2END7|N1END3|E1END3|S1END3|W1END3]",
    "JW2BEG[7|7|7|7|7|7|7|7],[S1END2|NN4END0|E2END0|S2END0|N1END0|E1END0|S1END0|W1END0]",

    "N1BEG[0|0|0|0],[J_l_CD_END1|JW2END3|J2MID_CDb_END3]",
    "N1BEG[1|1|1|1],[J_l_EF_END2|JW2END0|J2MID_EFb_END0]",
    "N1BEG[2|2|2|2],[J_l_GH_END3|JW2END1|J2MID_GHb_END1]",
    "N1BEG[3|3|3|3],[J_l_AB_END0|JW2END2|J2MID_ABb_END2]",

    "E1BEG[0|0|0|0],[J_l_CD_END1|JN2END3|J2MID_CDb_END3]",
    "E1BEG[1|1|1|1],[J_l_EF_END2|JN2END0|J2MID_EFb_END0]",
    "E1BEG[2|2|2|2],[J_l_GH_END3|JN2END1|J2MID_GHb_END1]",
    "E1BEG[3|3|3|3],[J_l_AB_END0|JN2END2|J2MID_ABb_END2]",

    "S1BEG[0|0|0|0],[J_l_CD_END1|JE2END3|J2MID_CDb_END3]",
    "S1BEG[1|1|1|1],[J_l_EF_END2|JE2END0|J2MID_EFb_END0]",
    "S1BEG[2|2|2|2],[J_l_GH_END3|JE2END1|J2MID_GHb_END1]",
    "S1BEG[3|3|3|3],[J_l_AB_END0|JE2END2|J2MID_ABb_END2]",

    "W1BEG[0|0|0|0],[J_l_CD_END1|JS2END3|J2MID_CDb_END3]",
    "W1BEG[1|1|1|1],[J_l_EF_END2|JS2END0|J2MID_EFb_END0]",
    "W1BEG[2|2|2|2],[J_l_GH_END3|JS2END1|J2MID_GHb_END1]",
    "W1BEG[3|3|3|3],[J_l_AB_END0|JS2END2|J2MID_ABb_END2]",

    "N4BEG[0|0|0|0],[N4END1|N2END2|E6END1]",
    "N4BEG[1|1|1|1],[N4END2|N2END3|E6END0]",
    "N4BEG[2|2|2|2],[N4END3|N2END0|W6END1]",
    "N4BEG[3|3|3|3],[N4END0|N2END1|W6END0]",

    "S4BEG[0|0|0|0],[S4END1|S2END2|E6END1]",
    "S4BEG[1|1|1|1],[S4END2|S2END3|E6END0]",
    "S4BEG[2|2|2|2],[S4END3|S2END0|W6END1]",
    "S4BEG[3|3|3|3],[S4END0|S2END1|W6END0]",

    "EE4BEG[0|0|0|0|0|0|0|0],[J2MID_ABb_END1|J2MID_CDb_END1|J2END_GH_END0|N1END2|S1END2|E1END2]",
    "EE4BEG[1|1|1|1|1|1|1|1],[J2MID_ABa_END2|J2MID_CDa_END2|J2END_EF_END0|N1END3|S1END3|E1END3]",
    "EE4BEG[2|2|2|2|2|2|2|2],[J2MID_EFb_END1|J2MID_GHb_END1|J2END_CD_END0|N1END0|S1END0|E1END0]",
    "EE4BEG[3|3|3|3|3|3|3|3],[J2MID_EFa_END2|J2MID_GHa_END2|J2END_AB_END0|N1END1|S1END1|E1END1]",

    "WW4BEG[0|0|0|0|0|0|0|0],[J2MID_ABb_END1|J2MID_CDb_END1|J2END_GH_END2|N1END2|S1END2|W1END2]",
    "WW4BEG[1|1|1|1|1|1|1|1],[J2MID_ABa_END2|J2MID_CDa_END2|J2END_EF_END2|N1END3|S1END3|W1END3]",
    "WW4BEG[2|2|2|2|2|2|2|2],[J2MID_EFb_END1|J2MID_GHb_END1|J2END_CD_END2|N1END0|S1END0|W1END0]",
    "WW4BEG[3|3|3|3|3|3|3|3],[J2MID_EFa_END2|J2MID_GHa_END2|J2END_AB_END2|N1END1|S1END1|W1END1]",

    "NN4BEG[0|0|0|0|0|0|0|0],[J2MID_ABb_END1|J2MID_CDb_END1|J2END_GH_END1|E1END2|W1END2|N1END2]",
    "NN4BEG[1|1|1|1|1|1|1|1],[J2MID_ABa_END2|J2MID_CDa_END2|J2END_EF_END1|E1END3|W1END3|N1END3]",
    "NN4BEG[2|2|2|2|2|2|2|2],[J2MID_EFb_END1|J2MID_GHb_END1|J2END_CD_END1|E1END0|W1END0|N1END0]",
    "NN4BEG[3|3|3|3|3|3|3|3],[J2MID_EFa_END2|J2MID_GHa_END2|J2END_AB_END1|E1END1|W1END1|N1END1]",

    "SS4BEG[0|0|0|0|0|0|0|0],[J2MID_ABb_END1|J2MID_CDb_END1|J2END_GH_END3|E1END2|W1END2|N1END2]",
    "SS4BEG[1|1|1|1|1|1|1|1],[J2MID_ABa_END2|J2MID_CDa_END2|J2END_EF_END3|E1END3|W1END3|N1END3]",
    "SS4BEG[2|2|2|2|2|2|2|2],[J2MID_EFb_END1|J2MID_GHb_END1|J2END_CD_END3|E1END0|W1END0|N1END0]",
    "SS4BEG[3|3|3|3|3|3|3|3],[J2MID_EFa_END2|J2MID_GHa_END2|J2END_AB_END3|E1END1|W1END1|N1END1]",

    "E6BEG[0|0|0|0|0|0|0|0],[J2MID_ABb_END1|J2MID_CDb_END1|J2MID_EFb_END1|J2MID_GHb_END1|E1END3|W1END3]",
    "E6BEG[1|1|1|1|1|1|1|1],[J2MID_ABa_END2|J2MID_CDa_END2|J2MID_EFa_END2|J2MID_GHa_END2|E1END2|W1END2]",

    "W6BEG[0|0|0|0|0|0|0|0],[J2MID_ABb_END1|J2MID_CDb_END1|J2MID_EFb_END1|J2MID_GHb_END1|E1END3|W1END3]",
    "W6BEG[1|1|1|1|1|1|1|1],[J2MID_ABa_END2|J2MID_CDa_END2|J2MID_EFa_END2|J2MID_GHa_END2|E1END2|W1END2]",

]
