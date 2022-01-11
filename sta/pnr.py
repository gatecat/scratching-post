import sys, os
from pathlib import Path

import CRL, Hurricane as Hur, Katana, Etesian, Anabatic, Cfg
from Hurricane import DataBase, Transformation, Box, Instance
from helpers import u, l, setNdaTopDir
from helpers.overlay import CfgCache, UpdateSession

sys.path.append("../../mpw4/thirdparty/open_pdk/C4M.Sky130/libs.tech/coriolis/techno/etc/coriolis2")
from node130 import sky130 as tech

tech.setup()
tech.StdCellLib_setup()

from plugins.alpha.block.block         import Block
from plugins.alpha.block.configuration import IoPin, GaugeConf
from plugins.alpha.block.spares        import Spares
from plugins.alpha.chip.configuration  import ChipConf
from plugins.alpha.chip.chip           import Chip
from plugins.alpha.core2chip.sky130    import CoreToChip

cell_name = "user_project_core"
cell = CRL.Blif.load(cell_name)

af = CRL.AllianceFramework.get()
env = af.getEnvironment()
env.setCLOCK('io_in_from_pad(0)')

lg5 = af.getRoutingGauge('StdCellLib').getLayerGauge( 5 )
lg5.setType( CRL.RoutingLayerGauge.PowerSupply )

conf = ChipConf( cell, ioPins=[], ioPads=[] ) 
conf.cfg.etesian.bloat               = 'Flexlib'
conf.cfg.etesian.uniformDensity      = True
conf.cfg.etesian.aspectRatio         = 1.0
# etesian.spaceMargin is ignored if the coreSize is directly set.
conf.cfg.etesian.spaceMargin         = 0.10
conf.cfg.etesian.antennaGateMaxWL = u(400.0)
conf.cfg.etesian.antennaDiodeMaxWL = u(800.0)
conf.cfg.etesian.feedNames = 'tie_diff,tie_diff_w2'
conf.cfg.anabatic.searchHalo         = 2
conf.cfg.anabatic.globalIterations   = 20
conf.cfg.anabatic.topRoutingLayer    = 'm4'
conf.cfg.katana.hTracksReservedLocal = 25
conf.cfg.katana.vTracksReservedLocal = 20
conf.cfg.katana.hTracksReservedMin   = 12
conf.cfg.katana.vTracksReservedMin   = 10
conf.cfg.katana.trackFill            = 0
conf.cfg.katana.runRealignStage      = True
conf.cfg.katana.dumpMeasures         = True
conf.cfg.katana.longWireUpReserve1   = 3.0
conf.cfg.block.spareSide             = u(7*10)
conf.cfg.chip.minPadSpacing          = u(1.46)
conf.cfg.chip.supplyRailWidth        = u(20.0)
conf.cfg.chip.supplyRailPitch        = u(40.0)
conf.cfg.harness.path                = "../../mpw4/resources/user_project_wrapper.def"
conf.useSpares           = True
# conf.useClockTree        = True
# conf.useHFNS             = True
conf.bColumns            = 2
conf.bRows               = 2
conf.chipName            = 'chip'
conf.coreSize            = ( u( 50*10.0), u( 50*10.0) )

conf.useHTree( 'io_in_from_pad(0)', Spares.HEAVY_LEAF_LOAD )

coreToChip = CoreToChip( conf )
coreToChip.buildChip()
chipBuilder = Chip( conf )
chipBuilder.doChipFloorplan()
chipBuilder.doPnR()
chipBuilder.save()

db = DataBase.getDB()
rootlib = db.getRootLibrary()


Path("export").mkdir(parents=True, exist_ok=True)
os.chdir("export")
lib = rootlib.getLibrary("StdCellLib")
CRL.LefExport.drive(lib, 1)
CRL.DefExport.drive(conf.corona, 0)
for cell in lib.getCells():
    if cell.getName() in (conf.corona.getName(), conf.core.getName(), conf.chip.getName()):
        continue
    CRL.DefExport.drive(cell, 0)
