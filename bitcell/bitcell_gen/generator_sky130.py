import gdspy

# GDS layers
L_PR_BNDRY  = (236, 0)
L_AREAID    = (81, 4)
L_NWELL     = (64, 20)
L_NWELL_PIN = (64, 16)
L_NWELL_LB  = (64, 5)
# L_LVPWELL  = (204, 0)
L_PWELL_PIN = (122, 16)
L_PWELL_LB  = (64, 59)
L_POLY      = (66, 20)
L_NSDM      = (93, 44)
L_PSDM      = (94, 20)
L_HVTP      = (78, 44)
L_LICON1    = (66, 44)
L_NPC       = (95, 20)
L_LI1       = (67, 20)
L_LI1_PIN   = (67, 16)
L_LI1_LB    = (67, 5)
L_MCON      = (67, 44)
L_MET1      = (68, 20)
L_MET1_PIN  = (68, 20)
L_MET1_LB   = (68, 5)

prim_size   = (460*15, 2720)

livia_size = (170, 170)
m1via_size = (170, 170)

well_extent = (190, 190)
nw_start = 1305
nsdm_end = 1015
psdm_start = 1935
hvt_start = 1250
npc_pos = (975, 1925)

rail_m1width  = 480
rail_liwidth  = 170
rail_viapitch = 460

def _rect(cell, p0, p1, l):
    rect = gdspy.Rectangle(p0, p1, layer=l[0], datatype=l[1])
    cell.add(rect)

def _label(cell, p, text, l, anchor="nw"):
    label = gdspy.Label(text, p, anchor, layer=l[0], texttype=l[1])
    cell.add(label)

def _port(cell, p, text, pin_l, lab_l, size=(170, 170), anchor="nw"):
    _rect(cell, (p[0] - size[0] // 2, p[1] - size[1] // 2), (p[0] + size[0] // 2, p[1] + size[1] // 2), pin_l)
    _label(cell, p, text, lab_l)

def _cont(cell, x, y):
    _rect(cell, (x - livia_size[0] // 2, y - livia_size[1] // 2), (x + livia_size[0] // 2, y + livia_size[1] // 2), L_LICON1)

def _via(cell, x, y):
    _rect(cell, (x - m1via_size[0] // 2, y - m1via_size[1] // 2), (x + m1via_size[0] // 2, y + m1via_size[1] // 2), L_MCON)

def add_rail(cell, y, name):
    _rect(cell, (0, y - rail_liwidth//2), (prim_size[0], y + rail_liwidth // 2), L_LICON1)
    _rect(cell, (0, y - rail_m1width//2), (prim_size[0], y + rail_m1width // 2), L_MET1)
    _port(cell, (rail_viapitch//2, y), name, L_MET1_PIN, L_MET1_LB)
    # via strip
    for i in range(prim_size[0] // rail_viapitch):
        _via(cell, (rail_viapitch // 2 + i * rail_viapitch), y)


def add_outline(cell):
    # Wells
    _rect(cell, (-well_extent[0], nw_start), (prim_size[0] + well_extent[0], prim_size[1] + well_extent[1]), L_NWELL)
    _port(cell, (rail_viapitch//2, prim_size[1]), "VPB", L_NWELL_PIN, L_NWELL_LB)
    _port(cell, (rail_viapitch//2, 0), "VNB", L_NWELL_PIN, L_NWELL_LB)
    # Implant
    _rect(cell, (0, -well_extent[1]), (prim_size[0], nsdm_end), L_NSDM)
    # TODO: complex NPC, PSDM shape?
    _rect(cell, (0, psdm_start), (prim_size[0] + well_extent[0], prim_size[1] + well_extent[1]), L_PSDM)
    _rect(cell, (0, npc_pos[0]), (prim_size[0], npc_pos[1]), L_NPC)
    # threshold (TODO: pass-fet out of HVT?)
    _rect(cell, (0, npc_pos[0]), (prim_size[0], npc_pos[1]), L_HVTP)
    # Markers
    _rect(cell, (0, 0), prim_size, L_PR_BNDRY)
    _rect(cell, (0, 0), prim_size, L_AREAID)
    # Power rails
    add_rail(cell, 0, "VGND")
    add_rail(cell, prim_size[1], "VPWR")


def _pwr_conn(cell, rail, x, y, w=230, ext=60):
    y0 = (rail_width//2) if rail == "VGND" else (prim_size[1] - rail_width//2)
    y1 = y + (via_size[1]//2 + ext) if rail == "VGND"  else y - (via_size[1]//2 + ext) 
    _rect(cell, (x-w//2, y0), (x+w//2, y1), L_MET1)
    _via(cell, x, y)

def add_logic(cell):
   pass

def main():
    lib = gdspy.GdsLibrary(unit=1e-09)
    cell = lib.new_cell("sky130_fpga_bitmux")
    add_outline(cell)
    add_logic(cell)
    lib.write_gds("sky130_fpga_bitmux.gds")

if __name__ == '__main__':
    main()
