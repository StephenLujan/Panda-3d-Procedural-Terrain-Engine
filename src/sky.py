"""
populator.py: This file handles all elements of an animated sky, affected by
the time of day. Additionally it will introduce lighting to the scene,
updated as appropriate for the skies condition.
"""
__author__ = "Stephen Lujan"


from panda3d.core import PNMImage
from pandac.PandaModules import AmbientLight
from pandac.PandaModules import Fog
from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import Texture
from pandac.PandaModules import TextureStage
from sun import *
from config import *

class ColoredByTime():
    def __init__(self):
        self.schedule = ((400, self.nightColor), (600, self.sunsetColor),
                         (900, self.dayColor), (1500, self.dayColor),
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
        self.skybox.setScale(1.5* MAX_VIEW_RANGE)
        self.skybox.setBin('background', 1)
        self.skybox.setDepthWrite(False)
        self.skybox.setDepthTest(False)
        self.skybox.setLightOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.setFogOff(1)
        self.skybox.hide(BitMask32.bit(2)) # Hide from the volumetric lighting camera

        self.dayColor = Vec4(.55, .65, .95, 1.0)
        self.nightColor = Vec4(.05, .05, .20, 1.0)
        self.sunsetColor = Vec4(.45, .5, .65, 1.0)
        ColoredByTime.__init__(self)
        self.setColor = self.skybox.setColor

    def setTime(self, time):
        self.colorize(time)
        

class DistanceFog(ColoredByTime):
    def __init__(self):

        self.exponential()
        render.attachNewNode(self.fog)
        render.setFog(self.fog)

        #self.dayColor = Vec4(0.73, 0.82, 0.90, 1.0)
        #self.dayColor = Vec4(0.57, 0.75, 0.94, 1.0)
        self.dayColor = Vec4(0.58, 0.66, 0.82, 1)
        self.nightColor = Vec4(-0.5, -0.3, .0, 1.0)
        self.sunsetColor = Vec4(0.75, .60, .65, 1.0)
        ColoredByTime.__init__(self)
        self.setColor = self.fog.setColor
        self.getColor = self.fog.getColor

    def setTime(self, time):
        self.colorize(time)

    def linear(self):
        self.fog = Fog("A linear-mode Fog node")
        self.fog.setLinearRange(0, 320)
        self.fog.setLinearFallback(5, 20, 50)

    def exponential(self):
        self.fog = Fog("Scene-wide exponential Fog object")
        density = 1.38629436 / (MAX_VIEW_RANGE + 30)
        self.fog.setExpDensity(density)


class CloudLayer(ColoredByTime):
    def __init__(self):

        tex1 = loader.loadTexture('textures/clouds.jpg')
        tex1.setMagfilter(Texture.FTLinearMipmapLinear)
        tex1.setMinfilter(Texture.FTLinearMipmapLinear)
        tex1.setAnisotropicDegree(2)
        tex1.setWrapU(Texture.WMRepeat)
        tex1.setWrapV(Texture.WMRepeat)
        tex1.setFormat(Texture.FAlpha)
        self.ts1 = TextureStage('clouds')
        #self.ts1.setMode(TextureStage.MBlend)
        self.ts1.setColor(Vec4(1, 1, 1, 1))

        #self.plane(-2000, -2000, 2000, 2000, 100)
        self.sphere(10000, -9600)

        self.clouds.setTransparency(TransparencyAttrib.MDual)
        self.clouds.setTexture(self.ts1, tex1)

        self.clouds.setBin('background', 3)
        self.clouds.setDepthWrite(False)
        self.clouds.setDepthTest(False)
        self.clouds.setTwoSided(True)
        self.clouds.setLightOff(1)
        self.clouds.setShaderOff(1)
        self.clouds.setFogOff(1)
        self.clouds.hide(BitMask32.bit(2)) # Hide from the volumetric lighting camera

        self.speed = 0.003
        self.time = 0
        self.dayColor = Vec4(0.98, 0.98, 0.95, 1.0)
        self.nightColor = Vec4(-0.5, -0.3, .0, 1.0)
        self.sunsetColor = Vec4(0.75, .60, .65, 1.0)
        ColoredByTime.__init__(self)
        self.setColor = self.clouds.setColor

    def plane(self, x1, y1, x2, y2, z):
        self.z = z
        maker = CardMaker('clouds')
        maker.setFrame(x1, x2, y1, y2)
        self.clouds = render.attachNewNode(maker.generate())
        self.clouds.setHpr(0, 90, 0)
        self.clouds.setTexOffset(self.ts1, 0, 1)
        self.clouds.setTexScale(self.ts1, 10, 10)

    def sphere(self, scale, z):
        self.z = z
        self.clouds = loader.loadModel("models/sphere")
        self.clouds.reparentTo(render)
        self.clouds.setHpr(0, 90, 0)
        self.clouds.setScale(scale)
        self.clouds.setTexOffset(self.ts1, 0, 1)
        self.clouds.setTexScale(self.ts1, 30, 12)

    def setTime(self, time):
        self.colorize(time)
        self.clouds.setTexOffset(self.ts1, self.time * self.speed, self.time * self.speed);

    def update(self, elapsed):
        self.time += elapsed
        self.clouds.setPos(base.cam.getPos(render) + Vec3(0, 0, self.z))

class Sky():
    def __init__(self, filters):

        self.skybox = SkyBox()
        self.sun = Sun(filters)
        self.clouds = CloudLayer()
        self.fog = DistanceFog()
        #self.addDirectLight()
        self.dayLength = 120 #in seconds
        self.setTime(800.0)
        self.previousTime = 0
        self.nightSkip = True
        self.paused = False

        ambient = Vec4(0.55, 0.65, 1.0, 1) #bright for hdr
        alight = AmbientLight('alight')
        alight.setColor(ambient)
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
        render.setShaderInput('alight0', alnp)

    def addDirectLight(self):
        """Adds just a direct light as an alternative to adding a Sun."""

        direct = Vec4(2.0, 1.9, 1.8, 1) #bright for hdr
        #direct = Vec4(0.7, 0.65, 0.6, 1)
        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(direct)
        dlnp = render.attachNewNode(self.dlight)
        render.setLight(dlnp)
        render.setShaderInput('dlight0', dlnp)
        return dlnp

    def setTime(self, time):
        self.time = time
        self.skybox.setTime(time)
        self.clouds.setTime(time)
        self.sun.setTime(time)
        self.fog.setTime(time)

    def start(self):
        self.updateTask = taskMgr.add(self.update, 'sky-update')

    def stop(self):
        if self.updateTask != None:
            taskMgr.remove(self.updateTask)

    def update(self, task):
        elapsed = task.time - self.previousTime
        self.previousTime = task.time

        self.clouds.update(elapsed)

        if self.paused:
            return task.cont
        if self.nightSkip:
            if self.time > 1925.0:
                self.time = 475.0
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