import gdspy

# GDS layers
L_PR_BNDRY = (0, 0)
L_NWELL    = (21, 0)
L_LVPWELL  = (204, 0)
L_COMP     = (22, 0)
L_DUALGATE = (55, 0)
L_POLY2    = (30, 0)
L_NPLUS    = (32, 0)
L_PPLUS    = (31, 0)
L_CONT     = (33, 0)
L_MET1     = (34, 0)
L_MET1_LB  = (34, 10)
L_V5_XTOR  = (112, 1)

prim_size  = (560*20, 3920)

via_size = (220, 220)
well_extent = (430, 430)
dgt_extent = (280, 280)
nw_start = 1760

rail_width = 600

def _rect(cell, p0, p1, l):
    rect = gdspy.Rectangle(p0, p1, layer=l[0], datatype=l[1])
    cell.add(rect)

def _label(cell, p, text, l, anchor="nw"):
    label = gdspy.Label(text, p, anchor, layer=l[0], texttype=l[1])
    cell.add(label)

def add_rail(cell, y, name):
    _rect(cell, (0, y - rail_width//2), (prim_size[0], y + rail_width // 2), L_MET1)
    _label(cell, (prim_size[0] // 2, y), name, L_MET1_LB)

def add_outline(cell):
    # Wells
    _rect(cell, (-well_extent[0], -well_extent[1]), (prim_size[0] + well_extent[0], nw_start), L_LVPWELL)
    _rect(cell, (-well_extent[0], nw_start), (prim_size[0] + well_extent[0], prim_size[1] + well_extent[1]), L_NWELL)
    # Dualgate
    _rect(cell, (-dgt_extent[0], -dgt_extent[1]), (prim_size[0] + dgt_extent[0], prim_size[1] + dgt_extent[1]), L_DUALGATE)
    # Markers
    _rect(cell, (0, 0), prim_size, L_PR_BNDRY)
    _rect(cell, (0, 0), prim_size, L_V5_XTOR)
    # Power rails
    add_rail(cell, 0, "VSS")
    add_rail(cell, prim_size[1], "VDD")

def main():
    lib = gdspy.GdsLibrary(unit=1e-09)
    cell = lib.new_cell("gf180mcu_fpga_bitmux")
    add_outline(cell)
    lib.write_gds("gf180mcu_fpga_bitmux.gds")

if __name__ == '__main__':
    main()
