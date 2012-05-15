"""
main.py: This file is the starting point for a demo of the Panda3d Procedural
Terrain Engine.

iModels: Jeff Styers, Reagan Heller, Gsk
Additional code from:
The panda3d roaming ralph demo, Gsk, Merlinson

This is my Panda 3d Terrain Engine.
My aim is to create the best possible 100% procedurally generated terrain
"""

__author__ = "Stephen Lujan"
__date__ = "$Oct 7, 2010 4:10:23 AM$"


from basicfunctions import *
from camera import *
from config import *
from creature import *
import direct.directbase.DirectStart
from direct.filter.CommonFilters import CommonFilters
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from gui import *
from pandac.PandaModules import LightRampAttrib
from pandac.PandaModules import PStatClient
from sky import *
from splashCard import *
from terrain import *
from waterNode import *
from mapeditor import *
from physics import *

#if __name__ == "__main__":
logging.info( "Hello World")

class World(DirectObject):

    def __init__(self):
        # set here your favourite background color - this will be used to fade to

        bgcolor = (0.2, 0.2, 0.2, 1)
        base.setBackgroundColor(*bgcolor)
        self.splash = SplashCard('textures/loading.png', bgcolor)
        taskMgr.doMethodLater(0.01, self.load, "Load Task")
        self.bug_text = addText(-0.95, "Loading...", True, scale=0.1)

    def load(self, task):

        PStatClient.connect()

        self.bug_text.setText("loading Display...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadDisplay()
        
        self.bug_text.setText("loading physics...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadPhysics()
        
        self.bug_text.setText("loading sky...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadSky()

        # Definitely need to make sure this loads before terrain
        self.bug_text.setText("loading terrain...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadTerrain()
        yield Task.cont
        yield Task.cont
        while taskMgr.hasTaskNamed("preloadTask"):
            #logging.info( "waiting")
            yield Task.cont
        logging.info( "terrain preloaded")

        #self.bug_text.setText("loading fog...")
        #showFrame()
        #self._loadFog()

        self.bug_text.setText("loading player...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadPlayer()
        
        self.bug_text.setText("loading water...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadWater()

        self.bug_text.setText("loading filters...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadFilters()
        
        self.bug_text.setText("loading gui controls...")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self._loadGui()

        self.bug_text.setText("loading miscellanious...")
        #showFrame()
        yield Task.cont
        yield Task.cont

        self.physics.setup(self.terrain, self.ralph)

        taskMgr.add(self.move, "moveTask")

        # Game state variables
        self.prevtime = 0
        self.isMoving = False
        self.firstmove = 1

        disableMouse()

        self.bug_text.setText("")
        #showFrame()
        yield Task.cont
        yield Task.cont
        self.splash.destroy()
        self.splash = None

        yield Task.done
        
    def _loadGui(self):
        try: 
            self.terrain.texturer.shader
        except: 
            logging.info( "Terrain texturer has no shader to control.")
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
        self.inst15 = addText(0.25, "[T]: Special Test")

        self.loc_text = addText(0.15, "[POS]: ", True)
        self.hpr_text = addText(0.10, "[HPR]: ", True)
        self.time_text = addText(0.05, "[Time]: ", True)

    def _loadTerrain(self):
        populator = TerrainPopulator()
        populator.addObject(makeTree, {}, 5)

        if SAVED_HEIGHT_MAPS:
            seed = 666
        else:
            seed = 0
        self.terrain = Terrain('Terrain', base.cam, MAX_VIEW_RANGE, populator, feedBackString=self.bug_text, id=seed)
        self.terrain.reparentTo(render)
        self.editor = MapEditor(self.terrain)

    def _loadWater(self):
        self._water_level = self.terrain.maxHeight * self.terrain.waterHeight
        size = self.terrain.maxViewRange * 1.5
        self.water = WaterNode(self, -size, -size, size, size, self._water_level)

    def _loadFilters(self):
        self.terrain.setShaderInput('waterlevel', self._water_level)

        # load default shaders
        cf = CommonFilters(base.win, base.cam)
        #bloomSize
        cf.setBloom(size='small', desat=0.7, intensity=1.5, mintrigger=0.6, maxtrigger=0.95)
        #hdrtype:
        render.setAttrib(LightRampAttrib.makeHdr1())
        #perpixel:
        render.setShaderAuto()
        #base.bufferViewer.toggleEnable()

    def _loadSky(self):
        self.sky = Sky(None)
        self.sky.start()

    def _loadPlayer(self):
        # Create the main character, Ralph
        
        self.ralph = Player(self.terrain.getElevation, 0, 0)
        self.focus = self.ralph
        self.terrain.setFocus(self.focus)
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
        self.accept("t", self.physics.test) #self.terrain.test)
        self.accept("e", self.toggleEditor)
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
        
        self.critter1 = Ai(self.terrain.getElevation, 2, 2)
        self.critter1.setSeek(self.ralph)
        
        self.critter2 = Ai(self.terrain.getElevation, 0, 0)
        self.critter2.maxSpeed = 5.0
        self.critter2.setWander(60)

    def _loadPhysics(self):
        self.physics = TerrainPhysics()

    def _loadPointLight(self):
        self.lightpivot = render.attachNewNode("lightpivot")
        self.lightpivot.hprinterval(10, Point3(360, 0, 0)).loop()
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
        except: logging.info( "No shader control found.")
        else: self.shaderControl.setHidden(ml)

    def toggleEditor(self):
        ml = toggleMouseLook()
        self.editor.toggle(not ml)

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
            deltaY *= -1
            
        if base.win.movePointer(0, 200, 200):
            self.camera.update(deltaX, deltaY)
            
        self.ralph.update(elapsed)
        self.critter1.update(elapsed)
        self.critter2.update(elapsed)

        self.terrain.setShaderInput("camPos", self.camera.camNode.getPos(render))
        self.terrain.setShaderInput("fogColor", self.sky.fog.getColor())
        #print self.sky.fog.fog.getColor()
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

def launchTerrainDemo():
    logging.info('instancing world...')
    w = World()
    logging.info('calling run()...')
    run()

#if __name__ == "__main__":
launchTerrainDemo()
