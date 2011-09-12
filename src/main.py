###
# Author: Stephen Lujan
# iModels: Jeff Styers, Reagan Heller, Gsk
# Additional code from:
# The panda3d roaming ralph demo, Gsk, Merlinson
#
# This is my Panda 3d Terrain Engine.
# My aim is to create the best possible 100% procedurally generated terrain
###

__author__ = "Stephen Lujan"
__date__ = "$Oct 7, 2010 4:10:23 AM$"

if __name__ == "__main__":
    print "Hello World"

import sys
import os

import direct.directbase.DirectStart
from direct.filter.CommonFilters import CommonFilters
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from pandac.PandaModules import LightRampAttrib
from pandac.PandaModules import PStatClient

from gui import *
from sky import *
from terrain import *
from waterNode import *
from creature import *
from camera import *
from basicfunctions import *
import splashCard

from panda3d.core import ConfigVariableInt
from panda3d.core import loadPrcFile
from pandac.PandaModules import Filename

###############################################################################
# Figure out what directory this program is in.
MYDIR = os.path.abspath(sys.path[0])
MYDIR = Filename.fromOsSpecific(MYDIR).getFullpath()
print('running from:' + MYDIR)

loadPrcFile("config/config.prc")

###############################################################################

class World(DirectObject):

    def __init__(self):
        # set here your favourite background color - this will be used to fade to

        bgcolor=(0, 0, 0, 1)
        base.setBackgroundColor(*bgcolor)
        self.splash = splashCard.splashCard('textures/loading.png', bgcolor)
        taskMgr.doMethodLater(0.01, self.load, "Load Task")
        self.bug_text = addText(-0.95, "Loading...", True, scale = 0.1)

    def load(self, task):
        #yield task.cont

        PStatClient.connect()

        self.bug_text.setText("loading Display...")
        showFrame()
        self._loadDisplay()

        self.bug_text.setText("loading sky...")
        showFrame()
        self._loadSky()

        # Definitely need to make sure this loads before terrain
        self.bug_text.setText("loading terrain...")
        showFrame()
        self._loadTerrain()

        self.bug_text.setText("loading fog...")
        showFrame()
        #self._loadFog()

        self.bug_text.setText("loading player...")
        showFrame()
        self._loadPlayer()
        
        self.bug_text.setText("loading water...")
        showFrame()
        self._loadWater()

        self.bug_text.setText("loading filters")
        showFrame()
        self._loadFilters()
        
        self.bug_text.setText("loading gui controls...")
        showFrame()
        self._loadGui()

        self.bug_text.setText("loading miscellanious")
        showFrame()
        
        taskMgr.add(self.move, "moveTask")

        # Game state variables
        self.prevtime = 0
        self.isMoving = False
        self.firstmove = 1

        disableMouse()

        self.bug_text.setText("")
        showFrame()
        self.splash.destroy()
        self.splash = None
        
    def _loadGui(self):
        try: 
            self.terrain.texturer.shader
        except: 
            print "Terrain texturer has no shader to control."
        else:
            self.shaderControl = TerrainShaderControl(-0.4, -0.1, self.terrain)
            self.shaderControl.hide()     

    def _loadDisplay(self):
        base.setFrameRateMeter(True)
        #base.win.setClearColor(Vec4(0, 0, 0, 1))
        # Post the instructions
        self.title = addTitle("Animate Dream Terrain Engine")
        self.inst1 = addText(0.95, "[ESC]: Quit")
        self.inst2 = addText(0.90, "[mouse wheel]: Camera Zoom")
        self.inst3 = addText(0.85, "[Y]: Y-axis Mouse Invert")
        self.inst4 = addText(0.80, "[W]: Run Ralph Forward")
        self.inst5 = addText(0.75, "[A]: Run Ralph Left")
        self.inst6 = addText(0.70, "[S]: Run Ralph Backward")
        self.inst7 = addText(0.65, "[D]: Run Ralph Right")
        self.inst8 = addText(0.60, "[shift]: Turbo Mode")
        self.inst9 = addText(0.55, "[R]: Regenerate Terrain")
        self.inst10 = addText(0.50, "[tab]: Open Shader Controls")
        self.inst11 = addText(0.45, "[1-8]: Set time to # * 3")
        self.inst12 = addText(0.40, "[N]: Toggle Night Skipping")
        self.inst13 = addText(0.35, "[P]: Pause day night cycle")
        self.inst14 = addText(0.3, "[F11]: Screen Shot")
        #self.inst15 = addText(0.25, "[T]: Special Test")
        

        self.loc_text = addText(0.15, "[POS]: ", True)
        self.hpr_text = addText(0.10, "[HPR]: ", True)
        self.time_text = addText(0.05, "[Time]: ", True)

    def _loadTerrain(self):
        maxRange = ConfigVariableInt("max-view-range", 400).getValue()
        self.terrain = Terrain('Terrain', base.camera, maxRange)
        self.terrain.reparentTo(render)

    def _loadWater(self):
        self._water_level = self.terrain.maxHeight * self.terrain.waterHeight
        size = self.terrain.maxViewRange * 1.5
        self.water = WaterNode(self, -size, -size, size, size, self._water_level)

    def _loadFilters(self):
        self.terrain.setShaderInput('waterlevel', self._water_level)

        # load default shaders
        cf = CommonFilters(base.win, base.cam)
        #bloomSize
        cf.setBloom(size='small', desat= 0.7, intensity = 1.5, mintrigger = 0.6, maxtrigger = 0.95)
        #hdrtype:
        render.setAttrib(LightRampAttrib.makeHdr1())
        #perpixel:
        render.setShaderAuto()
        #base.bufferViewer.toggleEnable()

    def _loadSky(self):
        self.sky = Sky()
        self.sky.start()

    def _loadPlayer(self):
        # Create the main character, Ralph
        ralphStartPosX = 50
        ralphStartPosY = 90
        ralphStartPosZ = self.terrain.getElevation(ralphStartPosX, ralphStartPosY)
        ralphStartPos = Vec3(ralphStartPosX,ralphStartPosY,ralphStartPosZ)
        
        self.ralph = Player(self.terrain.getElevation, ralphStartPos)
        self.focus = self.ralph
        self.terrain.focus = self.focus
        # Accept the control keys for movement
                
        self.camera = FollowCamera(self.ralph, self.terrain)
        self.mouseInvertY = False
        self.accept("escape", sys.exit)
        self.accept("w", self.ralph.setControl, ["forward", 1])
        self.accept("a", self.ralph.setControl, ["left", 1])
        self.accept("s", self.ralph.setControl, ["back", 1])
        self.accept("d", self.ralph.setControl, ["right", 1])
        self.accept("shift", self.ralph.setControl, ["turbo", 1])
        self.accept("f11", screenShot)
        self.accept("1", self.sky.setTime, [300.0])
        self.accept("2", self.sky.setTime, [600.0])
        self.accept("3", self.sky.setTime, [900.0])
        self.accept("4", self.sky.setTime, [1200.0])
        self.accept("5", self.sky.setTime, [1500.0])
        self.accept("6", self.sky.setTime, [1800.0])
        self.accept("7", self.sky.setTime, [2100.0])
        self.accept("8", self.sky.setTime, [0.0])
        self.accept("n", self.sky.toggleNightSkip)
        self.accept("p", self.sky.pause)
        self.accept("r", self.terrain.initializeHeightMap)
        self.accept("l", self.terrain.toggleWireFrame)
        self.accept("t", self.terrain.test)
        self.accept("w-up", self.ralph.setControl, ["forward", 0])
        self.accept("a-up", self.ralph.setControl, ["left", 0])
        self.accept("s-up", self.ralph.setControl, ["back", 0])
        self.accept("d-up", self.ralph.setControl, ["right", 0])
        self.accept("shift-up", self.ralph.setControl, ["turbo", 0])
        self.accept("wheel_up", self.camera.zoom, [1])
        self.accept("wheel_down", self.camera.zoom, [0])

        # mouse controls
        self.accept("tab", self.toggleMenu)
        self.mouseLook = True
        x = 0
        y = 0
        z = self.terrain.getElevation(x, y)
        self.critter1 = Ai(self.terrain.getElevation, Vec3(x,y,z))
        self.critter1.seekTarget = self.ralph


    def _loadPointLight():
        self.lightpivot = render.attachNewNode("lightpivot")
        self.lightpivot.hprInterval(10, Point3(360, 0, 0)).loop()
        plight = PointLight('plight')
        plight.setColor(Vec4(1, 1, 1, 1))
        plight.setAttenuation(Vec3(0.7, 0.05, 0))
        plnp = self.lightpivot.attachNewNode(plight)
        plnp.setPos(10, 0, 0)
        render.setLight(plnp)

        # create a sphere to denote the light
        sphere = loader.loadModel("models/sphere")
        sphere.reparentTo(plnp)
        render.setShaderInput("plight0", plnp)
    
    def toggleMenu(self):
        ml = toggleMouseLook()
        try: self.shaderControl
        except: print "No shader control found."
        else: self.shaderControl.setHidden(ml)
        
    def move(self, task):
        #self.lightpivot.setPos(self.focus.getPos() + Vec3(0, 0, 4))
        if not getMouseLook():
            return Task.cont

        elapsed = task.time - self.prevtime

        # use the mouse to look around and set Ralph's direction
        md = base.win.getPointer(0)
        deltaX = md.getX() -200
        deltaY = md.getY() -200
        if self.mouseInvertY:
            deltaY*= -1
            
        if base.win.movePointer(0, 200, 200):
            self.camera.update(deltaX,deltaY)
            
        self.ralph.update(elapsed)
        self.critter1.update(elapsed)

        self.terrain.setShaderInput("camPos", self.camera.camNode.getPos(render))
        self.terrain.setShaderInput("fogColor", self.sky.clouds.clouds.getColor()*0.9)
        #self.bug_text.setText('')
        # Ralph location output
        self.loc_text.setText('[LOC]: %03.1f, %03.1f,%03.1f ' % \
                              (self.ralph.getX(), self.ralph.getY(), self.ralph.getZ()))
        # camera heading + pitch output
        self.hpr_text.setText('[HPR]: %03.1f, %03.1f,%03.1f ' % \
                              (self.camera.fulcrum.getH(), self.camera.camNode.getP(), self.camera.camNode.getR()))

        self.time_text.setText('[Time]: %02i:%02i' % (self.sky.time / 100, self.sky.time % 100 * 60 / 100))

        # Store the task time and continue.
        self.prevtime = task.time
        return Task.cont

print('instancing world...')
w = World()

print('calling run()...')
run()
