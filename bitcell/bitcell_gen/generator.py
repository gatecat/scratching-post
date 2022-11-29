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

def _via(cell, x, y):
    _rect(cell, (x - via_size[0] // 2, y - via_size[0] // 2), (x + via_size[0] // 2, y + via_size[0] // 2), L_CONT)

def _pwr_conn(cell, rail, x, y, w=230, ext=60):
    y0 = (rail_width//2) if rail == "VSS" else (prim_size[1] - rail_width//2)
    y1 = y + (via_size[1]//2) + ext
    _rect(cell, (x-w//2, y0), (x+w//2, y1), L_MET1)
    _via(cell, x, y)

def _port(cell, x, y, name, ext=(120, 120)):
    _via(cell, x, y)
    _rect(cell, (x-ext[0], y-ext[1]), (x+ext[0], y+ext[1]), L_MET1)
    _label(cell, (x, y), name, L_MET1_LB)

def add_logic(cell):
    # transistor stripes for the bitcell part
    bx0 =  180
    ny0 =  780
    py1 = 3140
    ncw =  380
    pcw =  660

    bitpass_width = 1000 
    twoinv_width = 2400
    bx1 = bx0 + bitpass_width * 2 + twoinv_width

    _rect(cell, (bx0, ny0), (bx0+bitpass_width*2+twoinv_width, ny0+ncw), L_COMP) # Ndiff
    _rect(cell, (bx0+bitpass_width, py1-pcw), (bx0+bitpass_width+twoinv_width, py1), L_COMP) # Pdiff

    # wordline and access transistors
    # TODO: use gdspy polygons?
    wl_y0 = 120
    wl_y1 = 1440
    wl_gx = 700 # gate x-offset
    wl_gw = 600 # gate width
    wl_rw = 200 # route width
    wl_ry1 = wl_y0 + wl_rw
    wl_x0 = bx0 + (wl_gx - wl_gw // 2)
    wl_x1 = bx1 - (wl_gx - wl_gw // 2)
    # routing part
    _rect(cell, (wl_x0, wl_y0), (wl_x1, wl_ry1), L_POLY2)
    # gates
    _rect(cell, (wl_x0, wl_ry1), (wl_x0 + wl_gw, wl_y1), L_POLY2) # left (BL+)
    _rect(cell, (wl_x1 - wl_gw, wl_ry1), (wl_x1, wl_y1), L_POLY2) # right (BL-)
    # bitline contacts
    wl_bcx = 120
    _port(cell, bx0 + wl_bcx, ny0 + ncw // 2, "BLP")
    _port(cell, bx1 - wl_bcx, ny0 + ncw // 2, "BLN")
    # wordline contact
    wl_wcx = 200
    wl_wcy = 80
    wl_wcext = 200
    _rect(cell, (wl_x0, wl_y1), (wl_x0 + wl_gw, wl_y1 + wl_wcext), L_POLY2) # left (BL+)
    _port(cell, wl_x0 + wl_wcx, wl_y1 + wl_wcy, "WL")

def main():
    lib = gdspy.GdsLibrary(unit=1e-09)
    cell = lib.new_cell("gf180mcu_fpga_bitmux")
    add_outline(cell)
    add_logic(cell)
    lib.write_gds("gf180mcu_fpga_bitmux.gds")

if __name__ == '__main__':
    main()
