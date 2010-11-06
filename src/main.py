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
import direct.directbase.DirectStart
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
import os
from panda3d.core import BoundingBox
from pandac.PandaModules import AmbientLight
from pandac.PandaModules import CardMaker
from pandac.PandaModules import CullFaceAttrib
from pandac.PandaModules import DirectionalLight
from pandac.PandaModules import Filename
from pandac.PandaModules import Fog
from pandac.PandaModules import NodePath
from pandac.PandaModules import PandaNode
from pandac.PandaModules import Plane
from pandac.PandaModules import PlaneNode
from pandac.PandaModules import RenderState
from pandac.PandaModules import TextNode
from pandac.PandaModules import TransparencyAttrib
from pandac.PandaModules import Vec3
from pandac.PandaModules import Vec4
from pandac.PandaModules import WindowProperties
from pandac.PandaModules import PStatClient
from terrain import *

###############################################################################

SPEED = 0.5

# Figure out what directory this program is in.
MYDIR = os.path.abspath(sys.path[0])
MYDIR = Filename.fromOsSpecific(MYDIR).getFullpath()
print('running from:' + MYDIR)

# Function to put instructions on the screen.
def addInstructions(pos, msg):
	return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale=.05)

def addTextField(pos, msg):
	return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale=.05, mayChange=True)

# Function to put title on the screen.
def addTitle(text):
	return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1),
                        pos=(1.3, -0.95), align=TextNode.ARight, scale=.07)

##############################################################################


class WaterNode():

    def __init__(self, world, x1, y1, x2, y2, z):
        print('setting up water plane at z=' + str(z))

        # Water surface
        maker = CardMaker('water')
        maker.setFrame(x1, x2, y1, y2)

        world.waterNP = render.attachNewNode(maker.generate())
        world.waterNP.setHpr(0, -90, 0)
        world.waterNP.setPos(0, 0, z)
        world.waterNP.setTransparency(TransparencyAttrib.MAlpha)
        world.waterNP.setShader(loader.loadShader('shaders/water.sha'))
        world.waterNP.setShaderInput('wateranim', Vec4(0.03, -0.015, 64.0, 0)) # vx, vy, scale, skip
        # offset, strength, refraction factor (0=perfect mirror, 1=total refraction), refractivity
        world.waterNP.setShaderInput('waterdistort', Vec4(0.4, 4.0, 0.25, 0.45))

        # Reflection plane
        world.waterPlane = Plane(Vec3(0, 0, z + 1), Point3(0, 0, z))
        planeNode = PlaneNode('waterPlane')
        planeNode.setPlane(world.waterPlane)

        # Buffer and reflection camera
        buffer = base.win.makeTextureBuffer('waterBuffer', 512, 512)
        buffer.setClearColor(Vec4(0, 0, 0, 1))

        cfa = CullFaceAttrib.makeReverse()
        rs = RenderState.make(cfa)

        world.watercamNP = base.makeCamera(buffer)
        world.watercamNP.reparentTo(render)

        #sa = ShaderAttrib.make()
        #sa = sa.setShader(loader.loadShader('shaders/splut3Clipped.sha') )

        cam = world.watercamNP.node()
        cam.getLens().setFov(base.camLens.getFov())
        cam.getLens().setNear(1)
        cam.getLens().setFar(5000)
        cam.setInitialState(rs)
        cam.setTagStateKey('Clipped')
        #cam.setTagState('True', RenderState.make(sa))

        # ---- water textures ---------------------------------------------

        # reflection texture, created in realtime by the 'water camera'
        tex0 = buffer.getTexture()
        tex0.setWrapU(Texture.WMClamp)
        tex0.setWrapV(Texture.WMClamp)
        ts0 = TextureStage('reflection')
        world.waterNP.setTexture(ts0, tex0)

        # distortion texture
        tex1 = loader.loadTexture('textures/water.png')
        ts1 = TextureStage('distortion')
        world.waterNP.setTexture(ts1, tex1)

        # ---- Fog --- broken
        min = Point3(x1, y1, -999.0)
        max = Point3(x2, y2, z)
        boundry = BoundingBox(min, max)
        world.waterFog = Fog('waterFog')
        world.waterFog.setBounds(boundry)
        colour = (0.2, 0.5, 0.8)
        world.waterFog.setColor(*colour)
        world.waterFog.setExpDensity(0.05)
        render.attachNewNode(world.waterFog)
        #render.setFog(world.waterFog)

###############################################################################
class World(DirectObject):

    def __init__(self):

        #print(str(base.win.getGsg().getMaxTextureStages()) + ' texture stages available')
        base.setFrameRateMeter(True)
        PStatClient.connect()
        self.keyMap = {"left":0, "right":0, "forward":0, "back":0, "invert-y":0, "mouse":0, "turbo":0, "option+":0, "option-":0}
        base.win.setClearColor(Vec4(0, 0, 0, 1))
        # Post the instructions
        self.title = addTitle("Yet Another Roaming Ralph (Walking on uneven terrain too)")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.inst2 = addInstructions(0.90, "[mouse wheel]: Camera Zoom")
        self.inst3 = addInstructions(0.85, "[y]: Y-axis Mouse Invert")
        self.inst4 = addInstructions(0.80, "[w]: Run Ralph Forward")
        self.inst5 = addInstructions(0.75, "[a]: Run Ralph Left")
        self.inst6 = addInstructions(0.70, "[s]: Run Ralph Backward")
        self.inst7 = addInstructions(0.65, "[d]: Run Ralph Right")
        self.inst8 = addInstructions(0.60, "[shift]: Turbo Mode")
        self.inst9 = addInstructions(0.55, "[space]: Regenerate Terrain")

        self.bug_text = addTextField(0.50, "")
        self.loc_text = addTextField(0.45, "[LOC]: ")
        self.hpr_text = addTextField(0.40, "[HPR]: ")
        self.blend_text = addTextField(0.35, "Detail Texture Blend Mode: ")

        # Set up the environment
        # GeoMipTerrain
        self.terrain = Terrain('Terrain', base.camera)
        # Store the root NodePath for convenience
        #root = self.terrain.getRoot()
        #root.reparentTo(render)
        self.terrain.reparentTo(render)
        self.environ = self.terrain	# make available for original Ralph code below
        # some constants
        self._water_level = Vec4(0.0, 0.0, self.terrain.maxHeight
                                    * self.terrain.waterHeight, 1.0)

        # water
        self.water = WaterNode(self, -1000, -1000, 2000, 2000, self._water_level.getZ())
        # add some lighting
        ambient = Vec4(0.34, 0.3, 0.3, 1)
        direct = Vec4(0.74, 0.7, 0.7, 1)
        # ambient light
        alight = AmbientLight('alight')
        alight.setColor(ambient)
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
        # directional ("the sun")
        dlight = DirectionalLight('dlight')
        dlight.setColor(direct)
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(0.7, 0.2, -0.2)
        render.setLight(dlnp)

        # make waterlevel and lights available to the terrain shader
        self.terrain.setShaderInput('lightvec', Vec4(0.7, 0.2, -0.2, 1))
        self.terrain.setShaderInput('lightcolor', direct)
        self.terrain.setShaderInput('ambientlight', ambient)
        wl = self._water_level
        wl.setZ(wl.getZ()-0.05)	# add some leeway (gets rid of some mirroring artifacts)
        self.terrain.setShaderInput('waterlevel', self._water_level)

        # skybox
        self.skybox = loader.loadModel('models/skybox.egg')
        # make big enough to cover whole terrain, else there'll be problems with the water reflections
        self.skybox.setScale(1000)
        self.skybox.setBin('background', 1)
        self.skybox.setDepthWrite(0)
        self.skybox.setLightOff()
        self.skybox.reparentTo(render)

        # Create the main character, Ralph
        # ralphStartPos = self.environ.find("**/start_point").getPos()
        ralphStartPosX = 50
        ralphStartPosY = 90
        ralphStartPosZ = self.terrain.getElevation(ralphStartPosX, ralphStartPosY)
        self.ralph = Actor("models/ralph",
                           {"run":"models/ralph-run",
                           "walk":"models/ralph-walk"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.25)
        self.ralph.setPos(ralphStartPosX, ralphStartPosY, ralphStartPosZ)
        self.skybox.setPos(ralphStartPosX, ralphStartPosY, ralphStartPosZ)
        self.ralphHeight = 1.4  # to locate the top of Ralph's head for the camera to point at

        self.terrain.focus = self.ralph

        # Set the current viewing target for the mouse based controls
        #self.focus = Vec3(ralphStartPosX, ralphStartPosY+10, ralphStartPosZ+2)
        # Set up the camera
        self.camDistTarg = 6  # desired camera distance if no obsacles in the way
        self.camDist = self.camDistTarg
        self.testCamDist = self.camDistTarg
        self.mincamDist = 1.5 # for 3rd person camera
        self.maxcamDist = 100
        self.zcam = 0 # height of camera due to camera pitch in 3rd person
        self._setup_camera()
        base.camera.setPos(self.ralph.getX(), self.ralph.getY() + self.camDist, \
                           self.ralph.getZ() + self.ralphHeight)
        base.camera.lookAt(self.ralph)
        self.heading = base.camera.getH()
        self.oldheading = 0
        self.pitch = 0
        self.oldPitch = 0
        self.maxPitch = 70  # and used for minimum camera pitch too
        self.mousebtn = [0, 0, 0, 0]
        # parameter to enable inverting the mouse y-axis ( +1 is normal, -1 inverts)
        self.mouseNotInvertY = 1

        # Accept the control keys for movement
        self.accept("escape", sys.exit)
        self.accept("w", self.setKey, ["forward", 1])
        self.accept("a", self.setKey, ["left", 1])
        self.accept("s", self.setKey, ["back", 1])
        self.accept("d", self.setKey, ["right", 1])
        self.accept("y", self.setKey, ["invert-y", 1])
        self.accept("shift", self.setKey, ["turbo", 1])
        #self.accept("space", self.terrain.make )
        self.accept("l", self.terrain.toggleWireFrame )
        #self.accept("+", self.setKey, ["option+",1])
        #self.accept("-", self.setKey, ["option-",1])
        #self.accept("+", self.terrain.incrementDetailBlendMode )
        #self.accept("-", self.terrain.decrementDetailBlendMode )
        self.accept("w-up", self.setKey, ["forward", 0])
        self.accept("a-up", self.setKey, ["left", 0])
        self.accept("s-up", self.setKey, ["back", 0])
        self.accept("d-up", self.setKey, ["right", 0])
        self.accept("y-up", self.setKey, ["invert-y", 0])
        self.accept("shift-up", self.setKey, ["turbo", 0])
        #self.accept("+-up", self.setKey, ["option+",0])
        #self.accept("--up", self.setKey, ["option-",0])

        # mouse controls
        self.accept("mouse1", self.setMouseBtn, [0, 1])
        self.accept("mouse1-up", self.setMouseBtn, [0, 0])
        self.accept("mouse2", self.setMouseBtn, [1, 1])
        self.accept("mouse2-up", self.setMouseBtn, [1, 0])
        self.accept("mouse3", self.setMouseBtn, [2, 1])
        self.accept("mouse3-up", self.setMouseBtn, [2, 0])
        self.accept("wheel_up", self.setMouseBtn, [3, 1])
        self.accept("wheel_down", self.setMouseBtn, [3, -1])

        # ---- tasks -------------------------------------
        # Ralph movement
        taskMgr.add(self.move, "moveTask")

        # Game state variables
        self.prevtime = 0
        self.isMoving = False
        self.firstmove = 1

        # Create a ralphHead object for the camera to point at
        self.ralphHead = NodePath(PandaNode("ralphHead"))
        self.ralphHead.reparentTo(render)

        # create a test camera node for zooming out from 1st person
        self.testcam = NodePath(PandaNode("testcam"))
        self.testcam.reparentTo(render)

        # disable std. mouse
        base.disableMouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        self.bugstring = ''

	###########################################################################

    def _setup_camera(self):
        #sa = sa.setShader(loader.loadShader('shaders/stephen.sha'))
        #sa = self.terrain.shaderAttribute
        cam = base.cam.node()
        cam.getLens().setNear(1)
        cam.getLens().setFar(5000)
        cam.setTagStateKey('Normal')
        #cam.setTagState('True', RenderState.make(sa))

    def move(self, task):
        elapsed = task.time - self.prevtime
        if self.firstmove > 0:
            self.pitch = -9.0
            self.firstmove = 0
        # this is here to keep the camera pitch from decreasing once the camera is close to the ground
        # otherwise there is a delay as the camera is raised depending on how far it was pushed down
        x = base.camera.getX()
        y = base.camera.getY()
        z = 0.5 * self.ralphHeight + self.terrain.getElevation(x, y)
        rad1 = -self.pitch * math.pi / 180.0
        self.zcam = self.ralphHead.getZ() + self.camDist * 0.25 * (
                                                                   math.tan(rad1) + 3 * math.sin(rad1))

        # save Ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.
        # this doesn't work now, with collision detection removed, needs fixing
        startpos = self.ralph.getPos()

        # use the mouse to look around and set Ralph's direction
        isMouseTurning = False
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, 100, 100):
            self.heading -= (x - 100) * 0.2
            if abs(self.heading - self.oldheading) > 1: isMouseTurning = True
            tmp = self.mouseNotInvertY * (y - 100) * 0.2
            # don't keep decreasing the pitch after the camera can't move further
            if self.zcam > z: self.pitch -= tmp
            elif tmp > 0:  self.pitch -= tmp
        if self.pitch < -self.maxPitch: self.pitch = -self.maxPitch
        if self.pitch > self.maxPitch: self.pitch = self.maxPitch
        self.oldheading = self.heading

        # toggle mouse Y-axis invert
        if self.keyMap["invert-y"] != 0: self.mouseNotInvertY *= -1

        # If a move-key is pressed, move Ralph in the specified direction.
        direction = self.heading
        self.ralph.setHpr(direction, 0, 0)
        if self.camDist == 0: # 1st person view
            if self.heading > 0: base.camera.setH(self.heading - 180)
            else:  base.camera.setH(self.heading + 180)
        else: base.camera.setH(self.heading)
        turbo = 1 + 14 * self.keyMap["turbo"]
        if self.keyMap["left"] != 0:
            direction += 90.0
            self.ralph.setHpr(direction, 0, 0)
            self.ralph.setY(self.ralph, -elapsed * 35 * turbo)
        elif self.keyMap["right"] != 0:
            direction -= 90.0
            self.ralph.setHpr(direction, 0, 0)
            self.ralph.setY(self.ralph, -elapsed * 35 * turbo)
        elif self.keyMap["forward"] != 0:
            self.ralph.setY(self.ralph, -elapsed * 35 * turbo)
        elif self.keyMap["back"] != 0:
            self.ralph.setY(self.ralph, elapsed * 12 * turbo)

        # If Ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.
        # reversed walk animation for backward.
        if (self.keyMap["forward"] != 0) or (self.keyMap["left"] != 0) \
        or (self.keyMap["back"] != 0) or (self.keyMap["right"] != 0) or isMouseTurning:
            if self.isMoving is False:
                if (self.keyMap["forward"] != 0) or (self.keyMap["left"] != 0) \
                or (self.keyMap["right"] != 0) or isMouseTurning:
                    self.ralph.loop("run")
                else:
                    self.ralph.setPlayRate(-1, "walk")
                    self.ralph.loop("walk")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk", 5)
                self.isMoving = False

        # use terrain elevation to make Ralph stick to the ground
        x = self.ralph.getX()
        y = self.ralph.getY()
        self.ralph.setZ(self.terrain.getElevation(x, y))

        # ralphHead represents Ralph's head height
        # center the view near the top of his head
        self.ralphHead.setPos(self.ralph.getPos())
        self.ralphHead.setZ(self.ralph.getZ() + self.ralphHeight)
        self.ralphHead.setHpr(self.ralph.getHpr())

        # zoom in and out with the mouse wheel
        if self.mousebtn[3] > 0: # zoom in
            self.camDistTarg *= 0.909091
            self.mousebtn[3] = 0
        if self.mousebtn[3] < 0: # zoom out
            self.camDistTarg *= 1.1
            # jump from 1st to 3rd person on zoom out
            if self.camDistTarg == 0: self.camDistTarg = self.mincamDist
            self.mousebtn[3] = 0
        # jump from min distance to 1st person
        if self.camDistTarg < self.mincamDist: self.camDistTarg = 0
        if self.camDistTarg > self.maxcamDist: self.camDistTarg = self.maxcamDist

        # turn and run sideways instead of strafing due to lack of other animations
        # put the camera to the left of ralphHead for left direction
        if self.keyMap["left"] != 0:
            base.camera.setX(self.ralphHead, self.camDist + 0.1)
            base.camera.setY(self.ralphHead, 0.0)
            if self.camDistTarg > 0: # test camera position to enable clean zooming out
                self.testcam.setX(self.ralphHead, self.testCamDist + 0.1)
                self.testcam.setY(self.ralphHead, 0.0)
        # put the camera to the right of ralphHead for right direction
        elif self.keyMap["right"] != 0:
            base.camera.setX(self.ralphHead, -self.camDist-0.1)
            base.camera.setY(self.ralphHead, 0.0)
            if self.camDistTarg > 0:
                self.testcam.setX(self.ralphHead, -self.testCamDist + 0.1)
                self.testcam.setY(self.ralphHead, 0.0)
        # put the camera directly behind ralphHead for forward and back
        else:
            base.camera.setX(self.ralphHead, 0.0)
            base.camera.setY(self.ralphHead, self.camDist + 0.1)
            if self.camDistTarg > 0:
                self.testcam.setX(self.ralphHead, 0.0)
                self.testcam.setY(self.ralphHead, self.testCamDist + 0.1)

        # use terrain elevation for camera too
        # Keep the camera at least a bit above the terrain (sloppy way to reduce clipping)
        # reduce the camera distance if it tries to be too near the terrain
        x = base.camera.getX()
        y = base.camera.getY()
        # split up ralphHeight to allow the camera to go a bit lower, to look up a bit in 3rd person
        # this is the terrain elevation + half Ralph's height
        z = 0.5 * self.ralphHeight + self.terrain.getElevation(x, y)
        # this is the height of the camera due to pitch + Ralph's head position
        rad1 = -self.pitch * math.pi / 180.0
        self.zcam = self.ralphHead.getZ() + self.camDist * 0.25 * (
                                                                   math.tan(rad1) + 3 * math.sin(rad1))
        if self.camDist > 0:
            if self.zcam < z: # camera pitch is limited by the terrain, can't move lower
                base.camera.setZ(z)
            else:
                base.camera.setZ(self.zcam) # camera is free to move
            base.camera.lookAt(self.ralphHead)
            self.oldPitch = base.camera.getP()
            self.prevView = 'third'
        else:
            base.camera.setZ(z + 0.5 * self.ralphHeight)
            # messy way to make 3rd to 1st person view transition smoother when zooming in
            if self.prevView == 'third': self.pitch = self.oldPitch
            base.camera.setP(self.pitch)
            self.prevView = 'first'

        if self.camDistTarg > 0: # 3rd person view
            if self.zcam < z: # camera is too near the terrain
                self.testCamDist = self.camDist
                self.camDist *= .96 # reduce the camera distance
                if self.camDist < self.mincamDist: self.camDist = self.mincamDist
                if self.testCamDist < self.mincamDist: self.testCamDist = self.mincamDist
            else: # camera is free to move, try to return to target camera distance
                x = self.testcam.getX()
                y = self.testcam.getY()
                z = 0.5 * self.ralphHeight + self.terrain.getElevation(x, y)
                rad1 = -self.pitch * math.pi / 180.0
                self.zcam = self.ralphHead.getZ() + self.testCamDist * 0.25 * (
                                                                               math.tan(rad1) + 3 * math.sin(rad1))
                if self.zcam > z: # zoomed out test camera distance is ok
                    if self.camDist < self.camDistTarg: # want to zoom out
                        self.camDist = self.testCamDist
                        self.testCamDist *= 1.04
                    if self.camDist > self.camDistTarg: self.camDist = self.camDistTarg
                    if self.testCamDist > self.camDistTarg: self.testCamDist = self.camDistTarg
        else: self.camDist = 0 # 1st person view

        #self.bugstring = '%03.1f  :  %03.1f' % (self.pitch, self.camDist)
        # debug output
        if self.bugstring != '': self.bug_text.setText('[BUG]: %s' % self.bugstring)
        # Ralph location output
        self.loc_text.setText('[LOC]: %03.1f, %03.1f,%03.1f ' % \
                              (self.ralph.getX(), self.ralph.getY(), self.ralph.getZ()))
        # camera heading + pitch output
        self.hpr_text.setText('[HPR]: %03.1f, %03.1f,%03.1f ' % \
                              (base.camera.getH(), base.camera.getP(), base.camera.getR()))
        #current texture blending mode
        #self.blend_text.setText('[blend mode]: %i ' % \
        #                      ( self.terrain.textureBlendMode ) )

        # Time for water distortions
        render.setShaderInput('time', task.time)
        # move the skybox with the camera
        campos = base.camera.getPos()
        self.skybox.setPos(campos)
        # update matrix of the reflection camera
        mc = base.camera.getMat()
        mf = self.waterPlane.getReflectionMat()
        self.watercamNP.setMat(mc * mf)

        # Store the task time and continue.
        self.prevtime = task.time
        return Task.cont

    # records the state of the keyboard
    def setKey(self, key, value):
        self.keyMap[key] = value

    # records the state of the mouse
    def setMouseBtn(self, btn, value):
        self.mousebtn[btn] = value

print('instancing world...')
w = World()

print('calling run()...')
run()