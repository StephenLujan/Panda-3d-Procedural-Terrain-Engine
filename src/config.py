import sys

from direct.showbase import AppRunnerGlobal
import os
from panda3d.core import ConfigVariableBool
from panda3d.core import ConfigVariableInt
from panda3d.core import ConfigVariableDouble
from panda3d.core import loadPrcFile
from pandac.PandaModules import Filename
import logging

logging.basicConfig(level=logging.INFO,
                    format='*(%(threadName)-10s) %(filename)s:%(lineno)-4d %(message)s',)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug('debug messages working')

logging.basicConfig(level=logging.ERROR,
                    format='*(%(threadName)-10s) %(filename)s:%(lineno)-4d %(message)s',)

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


def getConfigInt(name, default):
    output = ConfigVariableInt(name, default).getValue()
    if RUNTYPE != 'python':
        if AppRunnerGlobal.appRunner.getTokenInt(name):
            output = AppRunnerGlobal.appRunner.getTokenInt(name)
    return output

def getConfigBool(name, default):
    output = ConfigVariableBool(name, default).getValue()
    if RUNTYPE != 'python':
        if AppRunnerGlobal.appRunner.getTokenBool(name):
            output = AppRunnerGlobal.appRunner.getTokenBool(name)
    return output

def getConfigDouble(name, default):
    output = ConfigVariableDouble(name, default).getValue()
    if RUNTYPE != 'python':
        if AppRunnerGlobal.appRunner.getTokenFloat(name):
            output = AppRunnerGlobal.appRunner.getTokenFloat(name)
    return output

def getConfigString(name, default):
    output = ConfigVariableString(name, default).getValue()
    if RUNTYPE != 'python':
        if AppRunnerGlobal.appRunner.getToken(name):
            output = AppRunnerGlobal.appRunner.getToken(name)
    return output


MAX_VIEW_RANGE = getConfigInt("max-view-range", 400)
MAX_TERRAIN_HEIGHT = getConfigDouble("max-terrain-height", 300.0)
TERRAIN_HORIZONTAL_STRETCH = getConfigDouble("terrain-horizontal-stretch", 1.0)


SAVED_HEIGHT_MAPS = getConfigBool("save-height-maps", False)
SAVED_SLOPE_MAPS = getConfigBool("save-slope-maps", False)
SAVED_TEXTURE_MAPS = getConfigBool("save-texture-maps", False)
SAVED_VEGETATION_MAPS = getConfigBool("save-vegetation-maps", False)

THREAD_LOAD_TERRAIN = getConfigBool("thread-load-terrain", False)
BRUTE_FORCE_TILES = getConfigBool("brute-force-tiles", True)