# To change this template, choose Tools | Templates
# and open the template in the editor.

from sun import *
from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import Texture
from pandac.PandaModules import TextureStage

class SkyBox():
    def __init__(self):
        #self.skybox = loader.loadModel('models/skydome')
        #self.skybox.setTexture(loader.loadTexture('models/early.png'))
        skynode = base.cam.attachNewNode('skybox')
        self.skybox = loader.loadModel("models/skybox")
        self.skybox.reparentTo(skynode)

        #self.skybox = loader.loadModel('models/rgbCube')
        
        self.skybox.setTextureOff(1)
        self.skybox.setShaderOff(1)
        # make big enough to cover whole terrain, else there'll be problems with the water reflections
        self.skybox.setScale(100)
        self.skybox.setBin('background', 1)
        self.skybox.setDepthWrite(False)
        self.skybox.setDepthTest(False)
        self.skybox.setLightOff(1)
        self.skybox.setShaderOff(1)
        self.skybox.hide(BitMask32.bit(2)) # Hide from the volumetric lighting camera
        
        self.dayColor = Vec4(.55,.65,.95,1.0)
        self.nightColor = Vec4(.0,.0,.1,1.0)
        self.sunsetColor = Vec4(.45,.45,.85,1.0)
        
    def setTime(self, time):
        # s = sunset strength [0,1]
        sc = self.skybox.setColor
        if time < 400.0 or time > 2000.0:
            sc(self.nightColor)
        elif time > 700.0 and time < 1700.0:
            sc(self.dayColor)
        elif time < 550.0:
            s = (time - 400.0) / 150.0
            sc(self.sunsetColor * s + self.nightColor * (1.0 - s))
        elif time < 700:
            s = (700.0 - time) / 150.0
            sc(self.sunsetColor * s + self.dayColor * (1.0 - s))
        elif time < 1850.0:
            s = (time - 1700.0)/ 150.0
            sc( self.sunsetColor * s + self.dayColor * (1.0 - s))
        elif time < 2000.0:
            s = (2000.0 - time) / 150.0
            sc( self.sunsetColor * s + self.nightColor * (1.0 - s))
            

class CloudLayer():
    def __init__(self):
        #maker = CardMaker('water')
        #maker.setFrame(-1, 1, -2, 2)
        #self.clouds = render.attachNewNode(maker.generate())
        
        self.clouds = loader.loadModel("models/skydome")
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
        self.clouds.setTexScale(self.ts1, 8, 2);
        #self.clouds.setTexRotate(self.ts1, degrees);
        # make big enough to cover whole terrain, else there'll be problems with the water reflections
        self.clouds.setScale(5000)
        self.clouds.setSz(2000)
        self.clouds.setBin('background', 1)
        self.clouds.setDepthWrite(False)
        self.clouds.setDepthTest(False)
        self.clouds.setLightOff(1)
        self.clouds.setShaderOff(1)
        self.clouds.hide(BitMask32.bit(2)) # Hide from the volumetric lighting camera
        #self.clouds.setHpr(0,90,0)
        
        self.dayColor = Vec4(1.0,1.0,1.0,1.0)
        self.nightColor = Vec4(.0,.0,.0,1.0)
        self.sunsetColor = Vec4(0.9,.8,.7,1.0)
        
    def setTime(self, time):
        # s = sunset strength [0,1]
        sc = self.clouds.setColor
        if time < 400.0 or time > 2000.0:
            sc(self.nightColor)
        elif time > 700.0 and time < 1700.0:
            sc(self.dayColor)
        elif time < 550.0:
            s = (time - 400.0) / 150.0
            sc(self.sunsetColor * s + self.nightColor * (1.0 - s))
        elif time < 700:
            s = (700.0 - time) / 150.0
            sc(self.sunsetColor * s + self.dayColor * (1.0 - s))
        elif time < 1850.0:
            s = (time - 1700.0)/ 150.0
            sc( self.sunsetColor * s + self.dayColor * (1.0 - s))
        elif time < 2000.0:
            s = (2000.0 - time) / 150.0
            sc( self.sunsetColor * s + self.nightColor * (1.0 - s))

        self.speed = 0.005
        self.clouds.setTexOffset(self.ts1, time * self.speed, time * self.speed);
        
    def setPos(self, pos):
        #pos.normalize()
        self.clouds.setPos(pos)
        #self.clouds.lookAt(base.cam)
        
    def update(self):
        self.setPos(base.cam.getPos()+Vec3(0,0,-600))
        
        
class Sky():
    def __init__(self):
        self.skybox = SkyBox()
        self.sun = Sun()
        self.clouds = CloudLayer()
        self.dayLength = 30 #in seconds
        self.setTime(500.0)
        self.previousTime = 0
        
    def setTime(self, time):
        self.time = time
        self.skybox.setTime(time)
        self.clouds.setTime(time)
        self.sun.setTime(time)

    def start(self):
        self.updateTask = taskMgr.add(self.update, 'sky-update')

    def stop(self):
        if self.updateTask != None:
            taskMgr.remove(self.updateTask)
            
    def update(self, task):
        elapsed = task.time - self.previousTime
        timeMultiplier = 2400.0 / self.dayLength
        self.previousTime = task.time
        self.clouds.update()
        #  start the next day at midnight
        #if self.time >= 2400.0:
        #    self.time -= 2400.0
        #  skip some night hours to make it interesting
        if self.time > 2200.0:
            self.time = 300.0
        self.setTime(self.time + elapsed * timeMultiplier)
        return task.cont