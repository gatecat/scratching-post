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
L_DIFF      = (65, 20)
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

prim_size   = (460*7, 2720)

livia_size = (170, 170)
m1via_size = (170, 170)

well_extent = (190, 190)
nw_start = 1305
nsdm_end = 1015
psdm_start = 1935
hvt_start = 1250
npc_pos = (685, 1925)

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
    assert isinstance(pin_l, list)
    for l in pin_l:
        _rect(cell, (p[0] - size[0] // 2, p[1] - size[1] // 2), (p[0] + size[0] // 2, p[1] + size[1] // 2), l)
    _label(cell, p, text, lab_l)

def _cont(cell, x, y):
    _rect(cell, (x - livia_size[0] // 2, y - livia_size[1] // 2), (x + livia_size[0] // 2, y + livia_size[1] // 2), L_LICON1)

def _via(cell, x, y):
    _rect(cell, (x - m1via_size[0] // 2, y - m1via_size[1] // 2), (x + m1via_size[0] // 2, y + m1via_size[1] // 2), L_MCON)

def add_rail(cell, y, name):
    _rect(cell, (0, y - rail_liwidth//2), (prim_size[0], y + rail_liwidth // 2), L_LI1)
    _rect(cell, (0, y - rail_m1width//2), (prim_size[0], y + rail_m1width // 2), L_MET1)
    _port(cell, (rail_viapitch//2, y), name, [L_MET1_PIN], L_MET1_LB)
    # via strip
    for i in range(prim_size[0] // rail_viapitch):
        _via(cell, (rail_viapitch // 2 + i * rail_viapitch), y)


def add_outline(cell):
    # Wells
    _rect(cell, (-well_extent[0], nw_start), (prim_size[0] + well_extent[0], prim_size[1] + well_extent[1]), L_NWELL)
    _port(cell, (rail_viapitch//2, prim_size[1]), "VPB", [L_NWELL_PIN], L_NWELL_LB)
    _port(cell, (rail_viapitch//2, 0), "VNB", [L_PWELL_PIN], L_PWELL_LB)
    # Implant
    _rect(cell, (0, -well_extent[1]), (prim_size[0], nsdm_end), L_NSDM)
    # TODO: complex NPC, PSDM shape?
    _rect(cell, (0, psdm_start), (prim_size[0] + well_extent[0], prim_size[1] + well_extent[1]), L_PSDM)
    _rect(cell, (0, npc_pos[0]), (prim_size[0], npc_pos[1]), L_NPC)
    # Markers
    _rect(cell, (0, 0), prim_size, L_PR_BNDRY)
    _rect(cell, (0, 0), prim_size, L_AREAID)
    # Power rails
    add_rail(cell, 0, "VGND")
    add_rail(cell, prim_size[1], "VPWR")


def _pwr_conn(cell, rail, x, y, w=170, ext=80):
    y0 = (rail_liwidth//2) if rail == "VGND" else (prim_size[1] - rail_liwidth//2)
    y1 = y + (livia_size[1]//2 + ext) if rail == "VGND"  else y - (livia_size[1]//2 + ext) 
    _rect(cell, (x-w//2, y0), (x+w//2, y1), L_LI1)
    _cont(cell, x, y)

def _liport(cell, p, name, ext):
    if len(ext) == 2:
        _rect(cell, (p[0] - ext[0] // 2, p[1] - ext[1] // 2), (p[0] + ext[0] // 2, p[1] + ext[1] // 2), L_LI1)
    elif len(ext) == 4:
        _rect(cell, (p[0] - ext[0], p[1] - ext[1]), (p[0] + ext[2], p[1] + ext[3]), L_LI1)
    _port(cell, p, name, [L_LICON1, L_LI1_PIN], L_LI1_LB)


def add_logic(cell):
    bx0 =  180+360
    ny0 =  235
    py1 = 2485
    ncw =  420
    pcw =  420
    ny = (ny0 + ncw // 2)
    py = (py1 - pcw // 2)

    rtpass_width = 700
    rtpass_gap = 700
    bitpass_width = 550 
    twoinv_width = 1000
    inv_sdx = 125

    bx1 = prim_size[0] - 280
    bxp = 180 + rtpass_width + rtpass_gap

    # diffusion for transistors
    _rect(cell, (bx0, ny0), (bx1, ny0+ncw), L_DIFF) # Ndiff
    _rect(cell, (bxp, py1-pcw), (bx1, py1), L_DIFF) # Pdiff
    # HVTP for bitcell but not mux...
    _rect(cell, (bxp - rtpass_gap // 2, hvt_start), (prim_size[0], prim_size[1]), L_HVTP)

    wl_y0 = 105
    wl_y1 = 800
    wl_gx = 335 # gate x-offset
    wl_gw = 150 # gate width
    wl_x0 = bx0 + (wl_gx - wl_gw // 2)
    wl_x1 = bx1 - (wl_gx - wl_gw // 2)
    # gates
    _rect(cell, (wl_x0, wl_y0), (wl_x0 + wl_gw, wl_y1), L_POLY) # left (BL+)
    _rect(cell, (wl_x1 - wl_gw, wl_y0), (wl_x1, wl_y1), L_POLY) # right (BL-)
    # bitline contacts
    wl_bcx = 125
    _liport(cell, (bx0 + wl_bcx, ny0 + ncw // 2), "BLP", (420, 165, 85, 165))
    _liport(cell, (bx1 - wl_bcx, ny0 + ncw // 2), "BLN", (85, 165, 240, 165))
    # wordline contacts
    wl_wcw = 285
    wl_wcy = 165
    wl_wcext = 330
    _rect(cell, (wl_x0 + wl_gw // 2 - wl_wcw // 2, wl_y1), (wl_x0 + wl_gw // 2 + wl_wcw // 2, wl_y1 + wl_wcext), L_POLY) # left 
    _liport(cell, (wl_x0 + wl_gw // 2, wl_y1 + wl_wcy), "WLA", (330, 165, 85, 165))
    _rect(cell, (wl_x1 - wl_gw // 2 - wl_wcw // 2, wl_y1), (wl_x1 - wl_gw // 2 + wl_wcw // 2, wl_y1 + wl_wcext), L_POLY) # right 
    _liport(cell, (wl_x1 - wl_gw // 2, wl_y1 + wl_wcy), "WLB", (85, 165, 330, 165))


    # inverter SD
    invnx0 = bx0 + bitpass_width
    invnx1 = bx1 - bitpass_width
    invpx1 = bxp + twoinv_width + inv_sdx * 2
    inv_spc = 420
    # SD N
    _cont(cell, invnx0, ny)
    invnxm = (invnx0 + invnx1) // 2
    _pwr_conn(cell, "VGND", invnxm, ny)
    _cont(cell, invnx1, ny)
    # SD P
    _cont(cell, invpx1-inv_sdx, py)
    invpxm = (invpx1 + bxp) // 2
    _pwr_conn(cell, "VPWR", invpxm, py)
    _cont(cell, bxp+inv_sdx, py)
    inv_gy0 = 105
    inv_gy1 = 2615
    inv_gw = 150
    inv_gmy = [1840, 1480]
    inv_gxn = [(3 * invnx0 + invnx1) // 4, (invnx0 + 3 * invnx1) // 4]
    inv_gxp = [(2 * (bxp+inv_sdx) + (invpx1 + bxp)) // 4, (2 * (invpx1-inv_sdx) + (invpx1 + bxp)) // 4]
    inv_qw = 170
    inv_qs = 170
    inv_qcm = [invnx0, invnx1]
    inv_qcw = 330
    inv_qrxn = [(invnxm - 440), (invnxm + 440)]
    inv_qrxp = [(bxp+inv_sdx), (invpx1-inv_sdx)]

    inv_qmy = [1950, 1685]

    for i in (0, 1):
        # inverter gate
        _rect(cell, (inv_gxn[i] - inv_gw // 2, inv_gy0), (inv_gxn[i] + inv_gw // 2, inv_gmy[i] - inv_gw // 2), L_POLY)
        _rect(cell, (inv_gxn[i] - inv_gw // 2, inv_gmy[i] - inv_gw // 2), (inv_gxp[i] + inv_gw // 2, inv_gmy[i] + inv_gw // 2), L_POLY)
        _rect(cell, (inv_gxp[i] - inv_gw // 2, inv_gmy[i] + inv_gw // 2), (inv_gxp[i] + inv_gw // 2, inv_gy1), L_POLY)
        # inverter Q (N part)
        _rect(cell, (inv_qcm[i] + (inv_qw // 2 if i == 1 else -inv_qw // 2), ny - inv_qcw // 2), (inv_qrxn[i] + (inv_qw // 2 if i == 1 else -inv_qw // 2), ny + inv_qcw // 2), L_LI1)
        _rect(cell, (inv_qrxn[i] - inv_qw // 2, ny - inv_qcw // 2), (inv_qrxn[i] + inv_qw // 2, inv_qmy[i] - inv_qw // 2), L_LI1)
        # inverter Q (across part)
        _rect(cell, (inv_qrxn[i] - inv_qw // 2, inv_qmy[i] - inv_qw // 2), (inv_qrxp[i] + inv_qw // 2, inv_qmy[i] + inv_qw // 2), L_LI1)
        # inverter Q (P part)
        _rect(cell, (inv_qrxp[i] - inv_qw // 2, inv_qmy[i] + inv_qw // 2), (inv_qrxp[i] + inv_qw // 2, py + inv_qcw // 2), L_LI1)
        # pins
        _port(cell, (inv_qrxn[i], inv_qmy[i]), "QP" if i == 0 else "QN", [L_LI1_PIN], L_LI1_LB)

    # inverter x-over
    inv_qdx0 = [inv_gxn[0] + inv_gw // 2, inv_gxn[1] - inv_gw // 2]
    inv_qdxc = [150, -150]
    inv_qdxr = [285, -285]
    inv_qdy = [1520, 970]
    inv_qh = 340
    for i in (0, 1):
        y1 = inv_qdy[i] + inv_qh // 2
        if y1 >= (inv_gmy[i] - inv_gw // 2 - 210):
            y1 = inv_gmy[i] - inv_gw // 2
        _rect(cell, (inv_qdx0[i], inv_qdy[i] - inv_qh // 2), (inv_qdx0[i] + inv_qdxr[i], y1), L_POLY)
        _cont(cell, inv_qdx0[i] + inv_qdxc[i], inv_qdy[i])
        _rect(cell, (inv_qdx0[i] + inv_qdxc[i] - ((inv_qw // 2) * (1-2*i)), inv_qdy[i] - inv_qcw // 2),  (inv_qdx0[i] + inv_qdxc[i] + ((inv_qw // 2) * (1-2*i)), inv_qdy[i] + inv_qcw // 2), L_LI1)
        # cross-brace
        _rect(cell, (inv_qdx0[i] + inv_qdxc[i] + ((inv_qw // 2) * (1-2*i)), inv_qdy[i] - inv_qcw // 2),  (inv_qrxn[1-i] - ((inv_qw // 2) * (1-2*i)), inv_qdy[i] + inv_qcw // 2), L_LI1)

    # pass pmos
    rx0 = 180
    rx1 = rx0 + rtpass_width
    r_bcx = 125
    r_lw = 330
    r_lh = 170
    ry = py1 - 190
    _rect(cell, (rx0, py1-pcw), (rx1, py1), L_DIFF) # Pdiff
    # ports
    _liport(cell, (rx0 + r_bcx, ry), "I", (120, 800, 85, 165))
    _liport(cell, (rx1 - r_bcx, ry), "O", (85, 800, 200, 165))
    r_gx = (rx0 + rx1) // 2
    r_gw = inv_gw
    r_gy1 = inv_gy1
    # gate
    _rect(cell, (r_gx - r_gw // 2, inv_gmy[0] - inv_gw // 2), (inv_gxn[0] - inv_gw // 2, inv_gmy[0] + inv_gw // 2), L_POLY)
    _rect(cell, (r_gx - r_gw // 2, inv_gmy[0] + inv_gw // 2), (r_gx + r_gw // 2, r_gy1), L_POLY)

def add_buf(cell):
    # inverter and level restorer part
    ix0 =  180
    ny0 =  235
    py1 = 2485
    ncw =  420
    pcw =  420
    ny = (ny0 + ncw // 2)
    py = (py1 - pcw // 2)

    lr_width = 700
    inv_width = 550
    ix1 = ix0 + lr_width + inv_width
    inv_sdx = 125
    _rect(cell, (ix0, ny0), (ix1, ny0+ncw), L_DIFF) # Ndiff
    _rect(cell, (ix0 + lr_width - inv_sdx, py1-pcw), (ix1, py1), L_DIFF) # Pdiff
    # inverter power
    _pwr_conn(cell, "VGND", ix0 + lr_width, ny)
    _pwr_conn(cell, "VPWR", ix0 + lr_width, py)
    # inverter output
    ri_bcx = 125
    ri_bc_ext = 330 // 2
    ri_w = 170
    _cont(cell, ix1 - ri_bcx, ny)
    _cont(cell, ix1 - ri_bcx, py)
    _rect(cell, (ix1 - ri_bcx - ri_w // 2, ny - ri_bc_ext), (ix1 - ri_bcx + ri_w // 2, py + ri_bc_ext), L_LI1)
    # inverter gate
    ri_gw = 150
    ri_gy0 = 105
    ri_gy1 = 2615
    ri_gx = ((ix0 + lr_width) + (ix1 - ri_bcx)) // 2
    _rect(cell, (ri_gx - ri_gw // 2, ri_gy0), (ri_gx + ri_gw // 2, ri_gy1), L_POLY)
    # input to restorer output
    lri_y0 = 1400
    lri_h = 330
    lri_w = 170
    _rect(cell, (ix0 - 50, lri_y0), (ri_gx - ri_gw // 2, lri_y0 + lri_h), L_POLY)
    # input contact
    _liport(cell, (ix0 + ri_bcx, lri_y0 + lri_h // 2), "I", (lri_w, lri_h))
    # restorer SD
    _rect(cell, (ix0 + ri_bcx - lri_w // 2, lri_y0), (ix0 + ri_bcx + lri_w // 2, ny - ri_bc_ext), L_LI1)
    _cont(cell, ix0 + ri_bcx, ny)
    # restorer gate
    lri_gy1 = 1150
    r_gx = ((ix0 + ri_bcx) + (ix0 + lr_width)) // 2
    lri_gdx = 210
    lri_gcx = 70
    _rect(cell, (r_gx - ri_gw // 2, ri_gy0), (r_gx + ri_gw // 2, lri_gy1), L_POLY)
    _rect(cell, (r_gx + ri_gw // 2, lri_gy1 - lri_h), (r_gx + lri_gdx, lri_gy1), L_POLY)
    _cont(cell, r_gx + lri_gcx, lri_gy1 - lri_h // 2)
    # restorer gate to inverter output
    _rect(cell, (r_gx + lri_gcx - 170 // 2, lri_gy1 - lri_h // 2 - 330 // 2), (ix1 - ri_bcx - ri_w // 2, lri_gy1 - lri_h // 2 + 330 // 2), L_LI1)
    # enableable driver
    drv_width = 1200
    dx0 = ix1 + 270
    dx1 = dx0 + drv_width
    _rect(cell, (dx0, ny0), (dx1, ny0+ncw), L_DIFF) # Ndiff
    _rect(cell, (dx0, py1-pcw), (dx1, py1), L_DIFF) # Pdiff
    d_bcx = 125
    d_ncx = d_bcx + 200
    # driver power straps
    _pwr_conn(cell, "VGND", dx0 + d_ncx, ny)
    _pwr_conn(cell, "VPWR", dx0 + d_bcx, py)
    # enable gate
    pg_gx = dx0 + d_bcx + 220
    pg_y0 = 1400
    pg_gdx = 210
    pg_gcx = 70
    _rect(cell, (pg_gx - ri_gw // 2, ri_gy1), (pg_gx + ri_gw // 2, pg_y0), L_POLY)
    _rect(cell, (pg_gx - pg_gdx, pg_y0 + lri_h), (pg_gx - ri_gw // 2, pg_y0), L_POLY)
    _liport(cell, (pg_gx - pg_gcx, pg_y0 + lri_h // 2), "OEB", (lri_w, lri_h))

    # driver gate
    dg_gx = pg_gx + 360
    _rect(cell, (dg_gx - ri_gw // 2, ri_gy0), (dg_gx + ri_gw // 2, ri_gy1), L_POLY)
    # driver gate contact
    dc_y0 = 820
    dc_h = 330
    _rect(cell, (dg_gx - ri_gw // 2, dc_y0), (dg_gx - ri_gw // 2 - pg_gdx, dc_y0 + dc_h), L_POLY)
    _cont(cell, dg_gx - ri_gw // 2 - pg_gcx, dc_y0 + dc_h // 2)
    _rect(cell, (dg_gx - ri_gw // 2 + 170 // 2, dc_y0 + dc_h // 2 - 330 // 2), (ix1 - ri_bcx + ri_w // 2, dc_y0 + dc_h // 2 + 330 // 2), L_LI1)
    # driver output
    _cont(cell, dx1 - d_bcx, ny)
    _cont(cell, dx1 - d_bcx, py)
    _rect(cell, (dx1 - d_bcx - ri_w // 2, ny - ri_bc_ext), (dx1 - d_bcx + ri_w // 2, py + ri_bc_ext), L_LI1)
    _port(cell, (dx1 - d_bcx, (ny + py // 2)), "O", [L_LI1_PIN], L_LI1_LB)

def main():
    global prim_size # yada yada ya
    lib = gdspy.GdsLibrary(unit=1e-09)
    cell = lib.new_cell("sky130_fpga_bitmux")
    add_outline(cell)
    add_logic(cell)
    cell = lib.new_cell("sky130_fpga_routebuf")
    prim_size   = (460*7, 2720) # TODO: make the buffer smaller if possible...
    add_outline(cell)
    add_buf(cell)
    lib.write_gds("sky130_fpga_bitmux.gds")

if __name__ == '__main__':
    main()
