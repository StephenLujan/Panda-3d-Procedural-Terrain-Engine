###
# Author: Stephen Lujan
# iModels: Jeff Styers, Reagan Heller, Gsk
# Additional code from:
# The panda3d roaming ralph demo, Gsk, Merlinson
#
# This is my Panda 3d Terrain Engine.
# My aim is to create the best possible 100% procedurally generated terrain
###

__author__ = "Stephen"
__date__ = "$Oct 7, 2010 4:10:23 AM$"

if __name__ == "__main__":
    print "Hello World"

import math
import sys

import os
from panda3d.core import ConfigVariableInt
from panda3d.core import loadPrcFile
from pandac.PandaModules import Filename

# Figure out what directory this program is in.
MYDIR = os.path.abspath(sys.path[0])
MYDIR = Filename.fromOsSpecific(MYDIR).getFullpath()
print('running from:' + MYDIR)

loadPrcFile("config/config.prc")

###############################################################################

import direct.directbase.DirectStart
from direct.filter.CommonFilters import CommonFilters
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from gui import *
from pandac.PandaModules import AmbientLight
from pandac.PandaModules import DirectionalLight
from pandac.PandaModules import LightRampAttrib
from pandac.PandaModules import NodePath
from pandac.PandaModules import PStatClient
from pandac.PandaModules import PandaNode
from pandac.PandaModules import PointLight
from pandac.PandaModules import RenderState
from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import TextNode
from pandac.PandaModules import Vec3
from pandac.PandaModules import Vec4
from pandac.PandaModules import WindowProperties
from sky import *
from terrain import *
from waterNode import *
from creature import *
from camera import *
import splashCard

###############################################################################

# Function returns the width / height ratio of the window or screen
def getScreenRatio():
    props = WindowProperties(base.win.getProperties())
    return float(props.getXSize()) / float(props.getYSize())

# Function to add instructions and other information along either side
def addText(pos, msg, changeable=False, alignLeft=True, scale=0.05):
    x = -getScreenRatio() + 0.03
    if alignLeft:
        align = TextNode.ALeft
    else:
        align = TextNode.ARight
        x *= -1.0
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1),
                        pos=(x, pos), align=align, scale=scale,
                        mayChange=changeable)

# Function to put title on the screen.
def addTitle(text):
    addText(-0.95, text, False, False, 0.07)

def showFrame():
    for i in range(4):
        base.graphicsEngine.renderFrame()

##############################################################################



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

        self.bug_text.setText("loading miscellanious")
        showFrame()
        
        taskMgr.add(self.move, "moveTask")

        # Game state variables
        self.prevtime = 0
        self.isMoving = False
        self.firstmove = 1

        # disable std. mouse
        base.disableMouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        self.bug_text.setText("loading gui controls...")
        showFrame()

        self.shaderControl = TerrainShaderControl(-0.4, -0.1, self.terrain)
        self.shaderControl.hide()

        self.bug_text.setText("")
        showFrame()
        self.splash.destroy()
        self.splash = None

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
        self.inst10 = addText(0.50, "[right-mouse]: Open Shader Controls")
        self.inst11 = addText(0.45, "[1-8]: Set time to # * 3")
        self.inst12 = addText(0.40, "[N]: Toggle Night Skipping")
        self.inst13 = addText(0.35, "[P]: Pause day night cycle")
        self.inst14 = addText(0.3, "[F11]: Screen Shot")
        

        self.loc_text = addText(0.20, "[LOC]: ", True)
        self.hpr_text = addText(0.15, "[HPR]: ", True)
        self.time_text = addText(0.10, "[Time]: ", True)
        #self.blend_text = addText(0.25, "Detail Texture Blend Mode: ")

    def _loadTerrain(self):
        maxRange=ConfigVariableInt("max-view-range").getValue()
        if maxRange:
            self.terrain = Terrain('Terrain', base.camera, maxRange=ConfigVariableInt("max-view-range").getValue())
        else:
            self.terrain = Terrain('Terrain', base.camera)
        self.terrain.reparentTo(render)
        self.environ = self.terrain	# make available for original Ralph code below

    def _loadWater(self):
        self._water_level = Vec4(0.0, 0.0, self.terrain.maxHeight
                                 * self.terrain.waterHeight, 1.0)
        size = self.terrain.maxViewRange * 1.5
        self.water = WaterNode(self, -size, -size, size, size, self._water_level.z)

    def _loadFilters(self):
        wl = self._water_level
        wl.z = wl.z-0.05	# add some leeway (gets rid of some mirroring artifacts)
        self.terrain.setShaderInput('waterlevel', self._water_level)

        # load default shaders
        cf = CommonFilters(base.win, base.cam)
        #bloomSize
        cf.setBloom(size='medium')
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
        # ralphStartPos = self.environ.find("**/start_point").getPos()
        ralphStartPosX = 50
        ralphStartPosY = 90
        ralphStartPosZ = self.terrain.getElevation(ralphStartPosX, ralphStartPosY)
        ralphStartPos = Vec3(ralphStartPosX,ralphStartPosY,ralphStartPosZ)
        
        self.ralph = Player(self.terrain.getElevation, ralphStartPos)
        self.focus = self.ralph
        self.terrain.focus = self.focus
        # Accept the control keys for movement
                
        self.controlMap = {"left":0, "right":0, "forward":0, "back":0, "invert-y":0, "turbo":0, "option+":0, "option-":0, "zoom in":0, "zoom out": 0}
        self.ralph.controls = self.controlMap
        self.camera = FollowCamera(self.ralph, self.controlMap, self.terrain)
        self.mouseInvertY = False
        self.accept("escape", sys.exit)
        self.accept("w", self.setControl, ["forward", 1])
        self.accept("a", self.setControl, ["left", 1])
        self.accept("s", self.setControl, ["back", 1])
        self.accept("d", self.setControl, ["right", 1])
        self.accept("y", self.setControl, ["invert-y", 1])
        self.accept("shift", self.setControl, ["turbo", 1])
        self.accept("f11", self.screenShot)
        self.accept("1", self.sky.setTime, [300.0])
        self.accept("2", self.sky.setTime, [600.0])
        self.accept("3", self.sky.setTime, [900.0])
        self.accept("4", self.sky.setTime, [1200.0])
        self.accept("5", self.sky.setTime, [1500.0])
        self.accept("6", self.sky.setTime, [1800.0])
        self.accept("7", self.sky.setTime, [2100.0])
        self.accept("8", self.sky.setTime, [0.0])
        self.accept("n", self.sky.toggleNightSkip )
        self.accept("p", self.sky.pause )
        self.accept("r", self.terrain.initializeHeightMap)
        self.accept("l", self.terrain.toggleWireFrame)
        #self.accept("f", self.terrain.flatten)
        #self.accept("+", self.setControl, ["option+",1])
        #self.accept("-", self.setControl, ["option-",1])
        #self.accept("+", self.terrain.incrementDetailBlendMode )
        #self.accept("-", self.terrain.decrementDetailBlendMode )
        self.accept("w-up", self.setControl, ["forward", 0])
        self.accept("a-up", self.setControl, ["left", 0])
        self.accept("s-up", self.setControl, ["back", 0])
        self.accept("d-up", self.setControl, ["right", 0])
        self.accept("y-up", self.setControl, ["invert-y", 0])
        self.accept("shift-up", self.setControl, ["turbo", 0])
        #self.accept("+-up", self.setControl, ["option+",0])
        #self.accept("--up", self.setControl, ["option-",0])
        self.accept("wheel_up", self.camera.zoom, [1])
        self.accept("wheel_down", self.camera.zoom, [0])

        # mouse controls
        self.accept("mouse3", self.toggleMouseLook)
        self.mouseLook = True
#        self.accept("mouse1", self.setControl, [0, 1])
#        self.accept("mouse1-up", self.setControl, [0, 0])
#        self.accept("mouse2", self.setControl, [1, 1])
#        self.accept("mouse2-up", self.setControl, [1, 0])
#        self.accept("mouse3", self.setControl, [2, 1])
#        self.accept("mouse3-up", self.setControl, [2, 0])
#        self.accept("wheel_up", self.setControl, [3, 1])
#        self.accept("wheel_down", self.setControl, [3, -1])

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
        
    def move(self, task):
        #self.lightpivot.setPos(self.focus.getPos() + Vec3(0, 0, 4))
        if not self.mouseLook:
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
            
        # toggle mouse Y-axis invert
        if self.controlMap["invert-y"] != 0:
            self.mouseInvertY = not self.mouseInvertY
            
        self.ralph.update(elapsed)
        self.critter1.update(elapsed)

        #self.bug_text.setText('')
        # Ralph location output
        self.loc_text.setText('[LOC]: %03.1f, %03.1f,%03.1f ' % \
                              (self.ralph.getX(), self.ralph.getY(), self.ralph.getZ()))
        # camera heading + pitch output
        self.hpr_text.setText('[HPR]: %03.1f, %03.1f,%03.1f ' % \
                              (base.camera.getH(), base.camera.getP(), base.camera.getR()))

        self.time_text.setText('[Time]: %02i:%02i' % (self.sky.time / 100, self.sky.time % 100 * 60 / 100))
        #current texture blending mode
        #self.blend_text.setText('[blend mode]: %i ' % \
        #                      ( self.terrain.textureBlendMode ) )

        # Store the task time and continue.
        self.prevtime = task.time
        return Task.cont

# records the state of the keyboard
    def setControl(self, control, value):
        self.controlMap[control] = value


    def toggleMouseLook(self):
        self.mouseLook = not self.mouseLook
        props = WindowProperties()
        props.setCursorHidden(self.mouseLook)
        self.shaderControl.setHidden(self.mouseLook)
        base.win.requestProperties(props)
        print "toggleMouseLook"

    def screenShot(self):
        base.screenshot()
        print 'screenshot taken.'

def setResolution():
    wp = WindowProperties()
    wp.setSize(1920, 1080)
    wp.setFullscreen(True)
    base.win.requestProperties(wp)

#setResolution()

print('instancing world...')
w = World()

print('calling run()...')
run()
