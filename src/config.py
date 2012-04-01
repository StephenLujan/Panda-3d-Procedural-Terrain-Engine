import sys

from direct.showbase import AppRunnerGlobal
import os
from panda3d.core import ConfigVariableBool
from panda3d.core import ConfigVariableInt
from panda3d.core import loadPrcFile
from pandac.PandaModules import Filename
import logging

logging.basicConfig(level=logging.INFO,
                    format='(%(threadName)-10s) %(message)s',)

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',)


loadPrcFile("config/config.prc")
# Figure out what directory this program is in.
MYDIR = os.path.abspath(sys.path[0])
MYDIR = Filename.fromOsSpecific(MYDIR).getFullpath()
logging.info(('running from:' + MYDIR))

#http://www.panda3d.org/forums/viewtopic.php?t=10222
if AppRunnerGlobal.appRunner is None:
    RUNTYPE = 'python'
else:
    logging.info("dom"+ str(AppRunnerGlobal.appRunner.dom))
    if AppRunnerGlobal.appRunner.dom:
        RUNTYPE = 'website'
    else:
        RUNTYPE = 'local'

SAVED_HEIGHT_MAPS = ConfigVariableBool("save-height-maps", False).getValue()
SAVED_SLOPE_MAPS = ConfigVariableBool("save-slope-maps", False).getValue()
SAVED_TEXTURE_MAPS = ConfigVariableBool("save-texture-maps", False).getValue()
SAVED_VEGETATION_MAPS = ConfigVariableBool("save-vegetation-maps", False).getValue()
MAX_VIEW_RANGE = ConfigVariableInt("max-view-range", 400).getValue()