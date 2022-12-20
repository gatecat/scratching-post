import gdspy

# GDS layers
L_PR_BNDRY  = (236, 0)
L_NWELL     = (64, 20)
L_NWELL_PIN = (64, 16)
L_NWELL_LAB = (64, 5)
# L_LVPWELL  = (204, 0)
L_PWELL_PIN = (122, 16)
L_PWELL_LAB = (64, 59)
L_POLY      = (66, 20)
L_NSDM      = (93, 44)
L_PSDM      = (94, 20)
L_HVTP      = (78, 44)
L_LICON1    = (66, 44)
L_NPC       = (95, 20)
L_LI1       = (67, 20)
L_LI1_PIN   = (67, 16)
L_LI1_LAB   = (67, 5)
L_MCON      = (67, 44)
L_MET1      = (68, 20)
L_MET1_PIN  = (68, 20)
L_MET1_LAB  = (68, 5)

prim_size   = (460*15, 2720)

livia_size = (170, 170)
m1via_size = (170, 170)

well_extent = (190, 190)
nw_start = 1305

rail_width = 480

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
    _rect(cell, (-pls_extent[0], -pls_extent[1]), (prim_size[0] + pls_extent[0], nw_start), L_NPLUS)
    _rect(cell, (-pls_extent[0], nw_start), (prim_size[0] + pls_extent[0], prim_size[1] + pls_extent[1]), L_PPLUS)
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
    y1 = y + (via_size[1]//2 + ext) if rail == "VSS"  else y - (via_size[1]//2 + ext) 
    _rect(cell, (x-w//2, y0), (x+w//2, y1), L_MET1)
    _via(cell, x, y)

def _port(cell, x, y, name, ext=(200, 200, 200, 200)):
    _via(cell, x, y)
    _rect(cell, (x-ext[0], y-ext[1]), (x+ext[2], y+ext[3]), L_MET1)
    _label(cell, (x, y), name, L_MET1_LB)

def add_logic(cell):
    # transistor stripes for the bitcell part
    bx0 =  180
    ny0 =  780
    py1 = 3140
    ncw =  380
    pcw =  660
    ny = (ny0 + ncw // 2)
    py = (py1 - pcw // 2)

    bitpass_width = 1100 
    twoinv_width = 3000
    bx1 = bx0 + bitpass_width * 2 + twoinv_width

    _rect(cell, (bx0, ny0), (bx0+bitpass_width*2+twoinv_width, ny0+ncw), L_COMP) # Ndiff
    _rect(cell, (bx0+bitpass_width, py1-pcw), (bx0+bitpass_width+twoinv_width, py1), L_COMP) # Pdiff

    # wordline and access transistors
    # TODO: use gdspy polygons?
    wl_y0 = 120
    wl_y1 = 1440
    wl_gx = 800 # gate x-offset
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
    wl_bcx = 180
    _port(cell, bx0 + wl_bcx, ny0 + ncw // 2, "BLP")
    _port(cell, bx1 - wl_bcx, ny0 + ncw // 2, "BLN")
    # wordline contact
    wl_wcx = 300
    wl_wcy = 80
    wl_wcext = 350
    _rect(cell, (wl_x0, wl_y1), (wl_x0 + wl_gw, wl_y1 + wl_wcext), L_POLY2) # left (BL+)
    _port(cell, wl_x0 + wl_wcx, wl_y1 + wl_wcy, "WL", ext=(200, 160, 200, 300))
    # the actual inverters
    i_x0 = bx0 + bitpass_width
    i_x1 = i_x0 + twoinv_width
    q_w = 330
    q_dx = 340
    q_dy = 200
    qpx  = i_x0 + q_dx
    qnx  = i_x1 - q_dx
    # Q signals and contacts
    _rect(cell, (qpx - q_w//2, ny - q_dy), (qpx + q_w//2, py + q_dy), L_MET1) # QP
    _label(cell, (qpx, ny), "QP", L_MET1_LB)
    _via(cell, qpx, ny)
    _via(cell, qpx, py)
    _rect(cell, (qnx - q_w//2, ny - q_dy), (qnx + q_w//2, py + q_dy), L_MET1) # QN
    _label(cell, (qnx, ny), "QN", L_MET1_LB)
    _via(cell, qnx, ny)
    _via(cell, qnx, py)
    # inverter power
    i_xp = (i_x0 + i_x1) // 2
    _pwr_conn(cell, "VSS", i_xp, ny)
    _pwr_conn(cell, "VDD", i_xp, py)
    # inverter gates
    i_gdx = 300
    i_gnw = 600
    i_gpw = 500
    i_gy0 = ny0 - 220
    i_gym = 1930
    i_gy1 = py1 + 220
    for i_gx0 in (i_xp - i_gdx - i_gnw, i_xp + i_gdx):
        _rect(cell, (i_gx0, i_gy0), (i_gx0 + i_gnw, i_gym), L_POLY2)
        _rect(cell, (i_gx0 + (i_gnw - i_gpw), i_gym), (i_gx0 + i_gnw, i_gy1), L_POLY2)
    # inverter strap
    i_sdy = 300
    i_sw = 330
    i_sgdx = 400
    i_sym = (ny + py) // 2
    for i in (0, 1): # QP -> QN or QN -> QP
        i_sx0 = (qnx - q_w//2) if i == 1 else (qpx + q_w//2)
        i_sx1 = (i_xp - i_gdx - i_sgdx) if i == 1 else (i_xp + i_gdx + i_sgdx)
        i_sy = i_sym + i_sdy if i == 1 else i_sym - i_sdy
        # strap on metal1 from output
        _rect(cell, (i_sx0, i_sy - i_sw // 2), (i_sx1, i_sy + i_sw // 2), L_MET1)
        # contact to poly2 of other gate
        _via(cell, (i_sx1 + i_sgdx // 2) if i == 1 else (i_sx1 - i_sgdx // 2), i_sy)
    # transmission gate
    tg_space = 360
    tg_width = 2000
    tx0 = bx1 + tg_space
    tx1 = tx0 + tg_width
    # transistor stripes for the gate part
    _rect(cell, (tx0, ny0), (tx1, ny0+ncw), L_COMP) # Ndiff
    _rect(cell, (tx0, py1-pcw), (tx1, py1), L_COMP) # Pdiff
    t_iow = 360
    # transmission gate IO
    _rect(cell, (tx0, ny0), (tx0+t_iow, py1), L_MET1) # I
    _label(cell, (tx0 + t_iow // 2, (ny0 + py1) // 2), "I", L_MET1_LB)
    _rect(cell, (tx1, ny0), (tx1-t_iow, py1), L_MET1) # O
    _label(cell, (tx1 - t_iow // 2, (ny0 + py1) // 2), "O", L_MET1_LB)
    # transmission gate contacts
    _via(cell, tx0 + t_iow // 2, ny)
    _via(cell, tx0 + t_iow // 2, py)
    _via(cell, tx1 - t_iow // 2, ny)
    _via(cell, tx1 - t_iow // 2, py)
    # transmission gate gates
    tg_gw = 600
    tg_ge = 220
    tx = (tx0 + tx1) // 2
    _rect(cell, (tx - tg_gw // 2, ny0 - tg_ge), (tx + tg_gw // 2, ny0 + ncw + tg_ge), L_POLY2)
    _rect(cell, (tx - tg_gw // 2, py1 - pcw - tg_ge), (tx + tg_gw // 2, py1 + tg_ge), L_POLY2)
    # transmission gate straps
    qp_sy = 1800
    qp_sw = 200
    # QP strap access
    _rect(cell, (tx - tg_gw // 2, ny0 + ncw + tg_ge), (tx + tg_gw // 2, qp_sy - qp_sw // 2), L_POLY2)
    # QP strap endpoint
    qp_sx0 = i_xp + i_gdx + i_gnw
    _rect(cell, (qp_sx0, qp_sy - qp_sw // 2), (tx + tg_gw // 2, qp_sy + qp_sw // 2), L_POLY2)
    # QN strap upper
    qn_sy0 = py1 + tg_ge + 150
    qn_sx0 = qnx + 900
    _rect(cell, (tx - tg_gw // 2, py1 - pcw - tg_ge), (tx + tg_gw // 2, qn_sy0), L_POLY2)
    _rect(cell, (qn_sx0, qn_sy0), (tx + tg_gw // 2, qn_sy0 + qp_sw), L_POLY2)
    # QN strap down
    qn_sdw = 400
    qn_sde = 300
    _rect(cell, (qn_sx0, py - qn_sde), (qn_sx0 + qn_sdw, qn_sy0), L_POLY2)
    # QN via
    _via(cell, qn_sx0 + qn_sdw // 2, py)
    # QN met1
    qn_m1w = 400
    _rect(cell, (qnx - q_w//2, py + q_dy - qn_m1w), (qn_sx0 + qn_sdw, py + q_dy), L_MET1)

def main():
    lib = gdspy.GdsLibrary(unit=1e-09)
    cell = lib.new_cell("gf180mcu_fpga_bitmux")
    add_outline(cell)
    add_logic(cell)
    lib.write_gds("gf180mcu_fpga_bitmux.gds")

if __name__ == '__main__':
    main()
