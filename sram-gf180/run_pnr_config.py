import os
import sys
from pathlib import Path
technoDir = "/home/gatecat/chipflow-backend/chipflow_backend/pdksetup/open_pdks/C4M.gf180mcu/libs.tech/coriolis"
openpdksDir = "/home/gatecat/chipflow-backend/chipflow_backend/pdksetup/open_pdks"

# This file is auto generated by ChipFlow backend
from coriolis import CRL
sys.path.insert(0, technoDir)
sys.path.insert(0, openpdksDir)
from node180 import gf180mcu as tech

tech.setup()
tech.StdCell5V0Lib_setup()

from gf180mcu import CoreToChip
