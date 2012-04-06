"""
sun.py is adapted from the Naith project
-*- coding: utf-8 -*-
Copyright Reinier de Blois

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import math

from pandac.PandaModules import BitMask32
from pandac.PandaModules import CardMaker
from pandac.PandaModules import ColorBlendAttrib
from pandac.PandaModules import DirectionalLight
from pandac.PandaModules import NodePath
from pandac.PandaModules import OmniBoundingVolume
from pandac.PandaModules import Point2
from pandac.PandaModules import Shader
from pandac.PandaModules import Texture
from pandac.PandaModules import TransparencyAttrib
from pandac.PandaModules import Vec3
from pandac.PandaModules import Vec4
from config import *

class Sun:
    """Represents the sun, handles godrays, etc."""
    def __init__(self, filters):
        self.filters = filters
        self.updateTask = None
        self.finalQuad = None

        self.sun = base.cam.attachNewNode('sun')
        loader.loadModel("models/sphere").reparentTo(self.sun)
        self.sun.setScale(0.08)
        self.sun.setTwoSided(True)
        self.sun.setColorScale(1.0, 1.0, 1.0, 1.0, 10001)
        self.sun.setLightOff(1)
        self.sun.setShaderOff(1)
        self.sun.setFogOff(1)
        self.sun.setCompass()
        self.sun.setBin('background', 2)
        self.sun.setDepthWrite(False)
        self.sun.setDepthTest(False)
        # Workaround an annoyance in Panda. No idea why it's needed.
        self.sun.node().setBounds(OmniBoundingVolume())     

        direct = Vec4(2.0, 1.9, 1.8, 1) #bright for hdr
        #direct = Vec4(0.7, 0.65, 0.6, 1)
        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(direct)
        dlnp = self.sun.attachNewNode(self.dlight)
        render.setLight(dlnp)
        render.setShaderInput('dlight0', dlnp)

        self.setTime(700.0)

        pandaVolumetricLighting = False


        if pandaVolumetricLighting:
            self.filters.setVolumetricLighting( dlnp )
        else:
            self.vlbuffer = base.win.makeTextureBuffer('volumetric-lighting', base.win.getXSize() / 2, base.win.getYSize() / 2)
            self.vlbuffer.setClearColor(Vec4(0, 0, 0, 1))
            cam = base.makeCamera(self.vlbuffer)
            cam.node().setLens(base.camLens)
            cam.reparentTo(base.cam)
            initstatenode = NodePath('InitialState')
            initstatenode.setColorScale(0, 0, 0, 1, 10000)
            initstatenode.setShaderOff(10000)
            initstatenode.setFogOff(1)
            initstatenode.setLightOff(10000)
            initstatenode.setMaterialOff(10000)
            initstatenode.setTransparency(TransparencyAttrib.MBinary, 10000)
            cam.node().setCameraMask(BitMask32.bit(2))
            cam.node().setInitialState(initstatenode.getState())
            self.vltexture = self.vlbuffer.getTexture()
            self.vltexture.setWrapU(Texture.WMClamp)
            self.vltexture.setWrapV(Texture.WMClamp)
            card = CardMaker('VolumetricLightingCard')
            card.setFrameFullscreenQuad()
            self.finalQuad = render2d.attachNewNode(card.generate())
            self.finalQuad.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingColor, ColorBlendAttrib.OFbufferColor))
            self.finalQuad.setShader(Shader.load("shaders/filter-vlight.cg"))
            self.finalQuad.setShaderInput('src', self.vltexture)
            self.finalQuad.setShaderInput('vlparams', 32, 0.95 / 32.0, 0.985, 0.5) # Note - first 32 is now hardcoded into shader for cards that don't support variable sized loops.
            self.finalQuad.setShaderInput('casterpos', 0.5, 0.5, 0, 0)
            # Last parameter to vlcolor is the exposure
            vlcolor = Vec4(1, 0.99, 0.80, 0.03)
            self.finalQuad.setShaderInput('vlcolor', vlcolor)

        self.start()

    def setPos(self, pos):
        pos.normalize()
        self.sun.setPos(pos)
        self.sun.lookAt(base.cam)

    def setTime(self, time):
        self.time = time
        if time < 500.0 or time > 1900.0:
            self.sun.hide()
            self.dlight.setColor(Vec4(0, 0, 0, 0))
            return

        self.sun.show()
        noonOffset = (1200.0 - time) / 600.0
        sunsetStrength = noonOffset * noonOffset

        directColor = Vec4(2.7, 2.5, 2.1, 1) #bright for hdr
        sunsetColor = Vec4(1.8, 1.1, 0.6, 1)

        if sunsetStrength < 1.0:
            directColor *= 1-sunsetStrength
            sunsetColor *= sunsetStrength
            #logging.info( str(directColor)+ str(sunsetColor))
            lightColor = directColor + sunsetColor

        else:
            maxSunsetStrength = (1.0 + 1.0 / 6.0) * (1.0 + 1.0 / 6.0)
            duskTime = maxSunsetStrength - 1.0
            duskMultiplier = ((1.0 + duskTime) - sunsetStrength) / duskTime
            #logging.info( duskMultiplier)
            if duskMultiplier < 0:
                lightColor = Vec4(0, 0, 0, 1)
            else:
                lightColor = sunsetColor * duskMultiplier
                
        lightColor.w = 1
        self.dlight.setColor(lightColor)

        directColor = Vec4(1.0, 1.0, 1.0, 1)
        sunsetColor = Vec4(1.0, 0.9, 0.7, 1)
        directColor *= 1-sunsetStrength
        sunsetColor *= sunsetStrength
        #logging.info( str(directColor)+ str(sunsetColor))
        lightColor = directColor + sunsetColor
        self.sun.setColorScale(lightColor, 1000)        

        if self.finalQuad != None:
            directColor = Vec4(1, 0.99, 0.80, 0.03)
            sunsetColor = Vec4(1, 0.65, 0.25, 0.025)
            sunsetColor *= sunsetStrength
            directColor *= 1-sunsetStrength
            vlColor = directColor + sunsetColor
            self.finalQuad.setShaderInput('vlcolor', vlColor)

        angle = noonOffset * math.pi / 2
        y = math.sin(angle)
        z = math.cos(angle)
        #logging.info( "sun angle, x, z: ", angle, x, z)
        self.setPos(Vec3(0, y, z))

    def start(self):
        if self.finalQuad != None:
            self.updateTask = taskMgr.add(self.update, 'sun-update')

    def stop(self):
        if self.updateTask != None:
            taskMgr.remove(self.updateTask)

    def update(self, task):
        casterpos = Point2()
        base.camLens.project(self.sun.getPos(base.cam), casterpos)
        self.finalQuad.setShaderInput('casterpos', Vec4(casterpos.getX() * 0.5 + 0.5, (casterpos.getY() * 0.5 + 0.5), 0, 0))

        return task.cont

