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
        world.waterNP.setShaderInput('time', 0)

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
