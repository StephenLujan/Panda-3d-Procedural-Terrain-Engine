# To change this template, choose Tools | Templates
# and open the template in the editor.

from pandac.PandaModules import AmbientLight
from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import Texture
from pandac.PandaModules import TextureStage
from pandac.PandaModules import Fog
from sun import *

class ColoredByTime():
    def __init__(self):
        self.schedule = ((400, self.nightColor), (600, self.sunsetColor),
                         (800, self.dayColor), (1600, self.dayColor),
                         (1800, self.sunsetColor), (2000, self.nightColor))

    def interpolateColor (self, start, end, time, startColor, endColor):
        ratio = (time - start) / (end - start + 0.000001)
        self.setColor(endColor * ratio + startColor * (1 - ratio))

    def colorize(self, time):
        lastPair = self.schedule[-1]
        for pair in self.schedule:
            if pair[0] > time:
                self.interpolateColor(pair[0], lastPair[0], time, pair[1], lastPair[1])
                break
            lastPair = pair

class SkyBox(ColoredByTime):
    def __init__(self):
        
        #self.skybox = loader.loadModel('models/skydome')
        #self.skybox.setTexture(loader.loadTexture('models/early.png'))
        skynode = base.cam.attachNewNode('skybox')
        self.skybox = loader.loadModel('models/rgbCube')
        self.skybox.reparentTo(skynode)
        
        self.skybox.setTextureOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.setTwoSided(True)
        # make big enough to cover whole terrain, else there'll be problems with the water reflections
        self.skybox.setScale(5000)
        self.skybox.setBin('background', 1)
        self.skybox.setDepthWrite(False)
        self.skybox.setDepthTest(False)
        self.skybox.setLightOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.setFogOff(1)
        self.skybox.hide(BitMask32.bit(2)) # Hide from the volumetric lighting camera
        
        self.dayColor = Vec4(.55, .65, .95, 1.0)
        self.nightColor = Vec4(.05, .05, .25, 1.0)
        self.sunsetColor = Vec4(.45, .5, .65, 1.0)
        ColoredByTime.__init__(self)
        self.setColor = self.skybox.setColor

    def setTime(self, time):
        self.colorize(time)

class DistanceFog(ColoredByTime):
    def __init__(self):
        #exponential
        #self.fog = Fog("Scene-wide exponential Fog object")
        #self.fog.setExpDensity(0.025)
        #linear
        self.fog = Fog("A linear-mode Fog node")
        self.fog.setLinearRange(0,320)
        self.fog.setLinearFallback(5,20,50)

        render.attachNewNode(self.fog)
        render.setFog(self.fog)

        self.dayColor = Vec4(1.0, 1.0, 1.0, 1.0)
        self.nightColor = Vec4(.0, .0, .0, 1.0)
        self.sunsetColor = Vec4(0.8, .65, .7, 1.0)
        ColoredByTime.__init__(self)
        self.setColor = self.fog.setColor

    def setTime(self, time):
        self.colorize(time)

class CloudLayer(ColoredByTime):
    def __init__(self):
        #maker = CardMaker('water')
        #maker.setFrame(-1, 1, -2, 2)
        #self.clouds = render.attachNewNode(maker.generate())
        
        self.clouds = loader.loadModel("models/sphere")
        tex1 = loader.loadTexture('textures/clouds_loop.png')
        tex1.setMagfilter(Texture.FTLinearMipmapLinear)
        tex1.setMinfilter(Texture.FTLinearMipmapLinear)
        tex1.setAnisotropicDegree(2)
        tex1.setWrapU(Texture.WMMirror)
        tex1.setWrapV(Texture.WMRepeat)
        #tex1.setWrapU(Texture.WMClamp)
        #tex1.setWrapV(Texture.WMClamp)
        self.ts1 = TextureStage('clouds')
        self.clouds.setTexture(self.ts1, tex1)
        self.clouds.setTransparency(TransparencyAttrib.MAlpha)
        self.clouds.reparentTo(render)
        self.clouds.setTexOffset(self.ts1, 0, 1);
        self.clouds.setTexScale(self.ts1, 20, 5);
        #self.clouds.setTexRotate(self.ts1, degrees);
        # make big enough to cover whole terrain, else there'll be problems with the water reflections
        self.clouds.setScale(5000)
        #self.clouds.setSz(1000)
        self.clouds.setBin('background', 3)
        self.clouds.setDepthWrite(False)
        self.clouds.setDepthTest(False)
        self.clouds.setTwoSided(True)
        self.clouds.setLightOff(1)
        self.clouds.setShaderOff(1)
        self.clouds.setFogOff(1)
        self.clouds.hide(BitMask32.bit(2)) # Hide from the volumetric lighting camera
        #self.clouds.setHpr(0,90,0)

        self.speed = 0.0005
        self.dayColor = Vec4(1.0, 1.0, 1.0, 1.0)
        self.nightColor = Vec4(-0.5, -0.3, .1, 1.0)
        self.sunsetColor = Vec4(0.75, .60, .65, 1.0)
        ColoredByTime.__init__(self)
        self.setColor = self.clouds.setColor

    def setTime(self, time):
        self.colorize(time)
        #self.clouds.setTexOffset(self.ts1, time * self.speed, time * self.speed);
        self.clouds.setHpr(0,time/90.0 ,90)
        #self.clouds.setTexOffset(self.ts1, time/600.0, time/600.0);
        
    def setPos(self, pos):
        #pos.normalize()
        self.clouds.setPos(pos)
        #self.clouds.lookAt(base.cam)
        
    def update(self):
        self.setPos(base.cam.getPos() + Vec3(0, 0, -4500))
        #self.setPos(base.cam.getPos()+Vec3(0,0,0))

        
class Sky():
    def __init__(self):
        self.skybox = SkyBox()
        self.sun = Sun()
        self.clouds = CloudLayer()
        #self.fog = DistanceFog()
        self.dayLength = 120 #in seconds
        self.setTime(800.0)
        self.previousTime = 0
        self.nightSkip = False
        self.paused = False
        
        ambient = Vec4(0.55, 0.65, 1.0, 1) #bright for hdr
        alight = AmbientLight('alight')
        alight.setColor(ambient)
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
        render.setShaderInput('alight0', alnp)
        
    def setTime(self, time):
        self.time = time
        self.skybox.setTime(time)
        self.clouds.setTime(time)
        self.sun.setTime(time)
        #self.fog.setTime(time)

    def start(self):
        self.updateTask = taskMgr.add(self.update, 'sky-update')

    def stop(self):
        if self.updateTask != None:
            taskMgr.remove(self.updateTask)
            
    def update(self, task):
        elapsed = task.time - self.previousTime
        self.previousTime = task.time

        self.clouds.update()

        if self.paused:
            return task.cont
        if self.nightSkip:
            if self.time > 2000.0:
                self.time = 400.0
        else:
            if self.time > 2400.0:
                self.time -= 2400.0
        timeMultiplier = 2400.0 / self.dayLength
        self.setTime(self.time + elapsed * timeMultiplier)
        return task.cont

    def toggleNightSkip(self):
        self.nightSkip = not self.nightSkip

    def pause(self):
        self.paused = not self.paused