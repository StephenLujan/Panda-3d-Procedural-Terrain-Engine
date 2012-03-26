# To change this template, choose Tools | Templates
# and open the template in the editor.

import os
import sys

from panda3d.core import ConfigVariableBool
from panda3d.core import ConfigVariableInt
from panda3d.core import loadPrcFile
from pandac.PandaModules import Filename

loadPrcFile("config/config.prc")
# Figure out what directory this program is in.
MYDIR = os.path.abspath(sys.path[0])
MYDIR = Filename.fromOsSpecific(MYDIR).getFullpath()
print('running from:' + MYDIR)

SAVED_HEIGHT_MAPS = ConfigVariableBool("save-height-maps", False).getValue()
SAVED_SLOPE_MAPS = ConfigVariableBool("save-slope-maps", False).getValue()
SAVED_TEXTURE_MAPS = ConfigVariableBool("save-texture-maps", False).getValue()
SAVED_VEGETATION_MAPS = ConfigVariableBool("save-vegetation-maps", False).getValue()
MAX_VIEW_RANGE = ConfigVariableInt("max-view-range", 400).getValue()