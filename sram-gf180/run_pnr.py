from run_pnr_config import *
from coriolis import CRL
from coriolis.CRL import Gds, LefImport
from coriolis.Hurricane import DataBase, Library, Transformation
from coriolis.plugins.block.spares import Spares
from coriolis.plugins.chip.configuration import ChipConf, BlockConf
from coriolis.plugins.chip.chip import Chip
from coriolis.plugins.block.block import Block
from coriolis.plugins.block.configuration import IoPin
from coriolis.Anabatic import StyleFlags
from coriolis.helpers import u


af = CRL.AllianceFramework.get()
env = af.getEnvironment()

rg = af.getRoutingGauge( "StdCell5V0Lib" )

db      = DataBase.getDB()
tech    = db.getTechnology()
rootlib = db.getRootLibrary()
sramLib   = Library.create(rootlib, 'sramlib')
LefImport.setMergeLibrary( sramLib )
LefImport.setGdsForeignDirectory("../")
LefImport.load( "/home/gatecat/test/sram_load/gf180mcu_fd_sc_mcu7t5v0__nom.lef" )
LefImport.load( "/home/gatecat/test/sram_load/gf180mcu_fd_ip_sram__sram512x8m8wm1.lef" )
af.wrapLibrary( sramLib, 1 )
# Gds.load(sramLib, "../gf180mcu_fd_ip_sram__sram512x8m8wm1.gds" , Gds.NoGdsPrefix|Gds.Layer_0_IsBoundary )

cell = CRL.Blif.load("upcounter_top")
env.setCLOCK("^sys_clk")
lg = af.getRoutingGauge("StdCell5V0Lib").getLayerGauge(5)
lg.setType(CRL.RoutingLayerGauge.PowerSupply)
ioPins = [
    ]
ioPads = [
    ]
conf = ChipConf( cell, ioPins=ioPins, ioPads=ioPads )
conf.cfg.anabatic.globalIterations = 20
conf.cfg.anabatic.searchHalo = 2
conf.cfg.anabatic.topRoutingLayer = "Metal3"
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

for instance in conf.core.getInstances():
    if "sram512x8" in instance.getMasterCell().getName():
        builder.placeMacro(instance.getName(), Transformation( u(160.0), u(160.0),  Transformation.Orientation.ID))
builder.doPnR()
if wrapPackage:
    package = ChipPackage( conf )
    package.wrapChip()
builder.save()
