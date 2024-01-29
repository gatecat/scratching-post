from run_pnr_config import *
from coriolis import CRL, Cfg
from coriolis.CRL import Gds, LefImport
from coriolis.Hurricane import DataBase, Library, Transformation, NetExternalComponents, Box, Net, Horizontal, Vertical, Rectilinear
from coriolis.plugins.block.spares import Spares
from coriolis.plugins.chip.configuration import ChipConf, BlockConf
from coriolis.plugins.chip.chip import Chip
from coriolis.plugins.block.block import Block
from coriolis.plugins.block.configuration import IoPin
from coriolis.Anabatic import StyleFlags
from coriolis.helpers import u, overlay, setTraceLevel
from coriolis.helpers.overlay import UpdateSession

import sys


af = CRL.AllianceFramework.get()
env = af.getEnvironment()

rg = af.getRoutingGauge( "StdCell5V0Lib" )

# with overlay.CfgCache(priority=Cfg.Parameter.Priority.UserFile) as cfg:
#     cfg.misc.verboseLevel2 = False
#     cfg.misc.minTraceLevel = 101
#     cfg.misc.maxTraceLevel = 102

db      = DataBase.getDB()
tech    = db.getTechnology()
rootlib = db.getRootLibrary()
sramLib   = Library.create(rootlib, 'sramlib')
LefImport.setMergeLibrary( sramLib )
LefImport.setGdsForeignDirectory("/home/gatecat/test/sram_load/")
LefImport.load( "/home/gatecat/test/sram_load/gf180mcu_fd_sc_mcu7t5v0__nom.lef" )
LefImport.load( "/home/gatecat/test/sram_load/gf180mcu_fd_ip_sram__sram512x8m8wm1.lef" )
af.wrapLibrary( sramLib, 1 )
# Gds.load(sramLib, "/home/gatecat/test/sram_load/gf180mcu_fd_ip_sram__sram512x8m8wm1.gds" , Gds.NoGdsPrefix|Gds.Layer_0_IsBoundary )
# assert False

sram = sramLib.getCell("gf180mcu_fd_ip_sram__sram512x8m8wm1")
with UpdateSession():
    met2 = rg.getLayerGauge( 1 )
    for net in sram.getNets():
        if net.getName() in ("VSS","VDD"):
            for component in net.getComponents():
                if isinstance(component, Horizontal) and component.getWidth() in (u(1.5), u(5)):
                    # Connect these (sensible) power strips
                    continue
                # Skip other power elements, that often cause offgrid vias
                NetExternalComponents.setInternal(component)


cell = CRL.Blif.load("upcounter_top")
env.setCLOCK("^sys_clk")
lg = af.getRoutingGauge("StdCell5V0Lib").getLayerGauge(4)
lg.setType(CRL.RoutingLayerGauge.PowerSupply)
ioPins = [
    ]
ioPads = [
    ]
conf = ChipConf( cell, ioPins=ioPins, ioPads=ioPads )
conf.cfg.anabatic.globalIterations = 20
conf.cfg.anabatic.searchHalo = 4
conf.cfg.anabatic.topRoutingLayer = "Metal5"
conf.cfg.block.spareSide = u(112)
conf.cfg.chip.minPadSpacing = u(1.46)
conf.cfg.chip.supplyRailPitch = u(64.0)
conf.cfg.chip.supplyRailWidth = u(32.0)
conf.cfg.etesian.antennaDiodeMaxWL = u(800.0)
conf.cfg.etesian.antennaGateMaxWL = u(400.0)
conf.cfg.etesian.aspectRatio = 1.0
conf.cfg.etesian.bloat = "Disabled"
conf.cfg.etesian.feedNames = "tie_poly,decap_w0"
conf.cfg.etesian.spaceMargin = 0.1
conf.cfg.etesian.uniformDensity = True
conf.cfg.harness.path = "/home/gatecat/chipflow-backend/chipflow_backend/pdksetup/efables/gf180/user_project_wrapper.def"
conf.cfg.katana.dumpMeasures = True
conf.cfg.katana.longWireUpReserve1 = 3.0
conf.cfg.katana.runRealignStage = True
conf.cfg.katana.trackFill = 0
conf.cfg.misc.verboseLevel1 = False
conf.cfg.misc.verboseLevel2 = False
conf.cfg.misc.minTraceLevel = 540
conf.cfg.misc.maxTraceLevel = 551
# setTraceLevel(540)

conf.bColumns = 2
conf.bRows = 2
conf.chipName = "chip"
conf.coreSize = [u(2912.0), u(2912.0)]
conf.useSpares = True
conf.useHTree("io_in_from_pad(0)", Spares.HEAVY_LEAF_LOAD)
buildChip = True
wrapPackage = False
if not buildChip:
    builder = Block( conf )
else:
    if wrapPackage:
        conf.coreToChipClass = CoreToChip
    else:
        coreToChip = CoreToChip( conf )
        coreToChip.buildChip()
    builder = Chip( conf )
    if wrapPackage:
        builder.doChipNetlist()
    builder.doChipFloorplan()

dx = 0
for instance in conf.core.getInstances():
    if "sram512x8" in instance.getMasterCell().getName():
        builder.placeMacro(instance.getName(), Transformation( dx, u(516),  Transformation.Orientation.MY))
        # builder.placeMacro(instance.getName(), Transformation( dx, u(2398.0),  Transformation.Orientation.ID))
        dx += instance.getMasterCell().getBoundingBox().getWidth()

with UpdateSession():
    wrapper_cell = rootlib.getCell("gf180mcu_fd_ip_sram_sram512x8m8wm1_wrapper")
    # create a big metal3 block, expanded to more than cover the macro, instead of lots of little blocks
    bb = Box( sram.getBoundingBox() )
    extra_block = Net.create(sram, "__blockage_2_")
    block_layer = rg.getLayerGauge( 2 ).getBlockageLayer()
    Horizontal.create(extra_block,
        block_layer,
        bb.getYCenter(),
        bb.getHeight(),
        bb.getXMin(),
        bb.getXMax()
    )
    block_layer = rg.getLayerGauge( 3 ).getBlockageLayer()
    Vertical.create(extra_block,
        block_layer,
        bb.getXCenter(),
        bb.getWidth() + u(2.0),
        bb.getYMin() - u(1.0),
        bb.getYMax() + u(1.0)
    )
    # sram.setAbutmentBox(Box(bb.getXMin(), bb.getYMin(), bb.getXMax(), bb.getYMax() + u(32)))


builder.doPnR()
if wrapPackage:
    package = ChipPackage( conf )
    package.wrapChip()
builder.save()
