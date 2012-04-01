"""
waterNode.py: This file contains the WaterNode used to render water in the
terrain. This code is originally based on the WaterNode class from the Yet
Another Roaming Ralph demo.
"""
__author__ = "Stephen Lujan"

from panda3d.core import BoundingBox
from pandac.PandaModules import CardMaker
from pandac.PandaModules import CullFaceAttrib
from pandac.PandaModules import Fog
from pandac.PandaModules import Plane
from pandac.PandaModules import PlaneNode
from pandac.PandaModules import Point3
from pandac.PandaModules import RenderState
from pandac.PandaModules import Shader
from pandac.PandaModules import ShaderPool
from pandac.PandaModules import Texture
from pandac.PandaModules import TextureStage
from pandac.PandaModules import TransparencyAttrib
from pandac.PandaModules import Vec3
from pandac.PandaModules import Vec4
from config import *

class WaterNode():
    def __init__(self, world, x1, y1, x2, y2, z):
        self.world = world
        logging.info(('setting up water plane at z=' + str(z)))

        # Water surface
        maker = CardMaker('water')
        maker.setFrame(x1, x2, y1, y2)

        self.waterNP = render.attachNewNode(maker.generate())
        self.waterNP.setHpr(0, -90, 0)
        self.waterNP.setPos(0, 0, z)
        self.waterNP.setTransparency(TransparencyAttrib.MAlpha)
        self.waterNP.setShader(loader.loadShader('shaders/water.sha'))
        self.waterNP.setShaderInput('wateranim', Vec4(0.03, -0.015, 64.0, 0)) # vx, vy, scale, skip
        # offset, strength, refraction factor (0=perfect mirror, 1=total refraction), refractivity
        self.waterNP.setShaderInput('waterdistort', Vec4(0.4, 4.0, 0.25, 0.45))
        self.waterNP.setShaderInput('time', 0)

        # Reflection plane
        self.waterPlane = Plane(Vec3(0, 0, z + 1), Point3(0, 0, z))
        planeNode = PlaneNode('waterPlane')
        planeNode.setPlane(self.waterPlane)

        # Buffer and reflection camera
        buffer = base.win.makeTextureBuffer('waterBuffer', 512, 512)
        buffer.setClearColor(Vec4(0, 0, 0, 1))

        cfa = CullFaceAttrib.makeReverse()
        rs = RenderState.make(cfa)

        self.watercamNP = base.makeCamera(buffer)
        self.watercamNP.reparentTo(render)

        #sa = ShaderAttrib.make()
        #sa = sa.setShader(loader.loadShader('shaders/splut3Clipped.sha') )

        cam = self.watercamNP.node()
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
        self.waterNP.setTexture(ts0, tex0)

        # distortion texture
        tex1 = loader.loadTexture('textures/water.png')
        ts1 = TextureStage('distortion')
        self.waterNP.setTexture(ts1, tex1)

        # ---- Fog --- broken
        min = Point3(x1, y1, -999.0)
        max = Point3(x2, y2, z)
        boundry = BoundingBox(min, max)
        self.waterFog = Fog('waterFog')
        self.waterFog.setBounds(boundry)
        colour = (0.2, 0.5, 0.8)
        self.waterFog.setColor(*colour)
        self.waterFog.setExpDensity(0.05)
        render.attachNewNode(self.waterFog)
        #render.setFog(world.waterFog)
        taskMgr.add(self.update, "waterTask")

    def update(self, task):
        # update matrix of the reflection camera
        mc = base.camera.getMat()
        mf = self.waterPlane.getReflectionMat()
        self.watercamNP.setMat(mc * mf)
        self.waterNP.setShaderInput('time', task.time)
        self.waterNP.setX(self.world.ralph.getX())
        self.waterNP.setY(self.world.ralph.getY())
        return task.cont
