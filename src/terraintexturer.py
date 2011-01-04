###
# Author: Stephen Lujan
###
# This file contains all of the TerrainTexturers
###

__author__="Stephen"
__date__ ="$Dec 15, 2010 2:14:33 AM$"


from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import Texture
from pandac.PandaModules import TextureStage
from panda3d.core import Shader
from pandac.PandaModules import Vec4
from pandac.PandaModules import Vec3
from terrainshadergenerator import *

###############################################################################
#   TerrainTexturer
###############################################################################

class TerrainTexturer():
    """Virtual Class"""

    def __init__(self, terrain):
        """initialize"""
        self.terrain = terrain

    def loadTexture(self, name):
        """A better texture loader"""
        tex = loader.loadTexture('textures/' + name)
        self.defaultFilters(tex)
        return tex

    def defaultFilters(self, texture):
        """Set a texture to use desired default filters."""
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        texture.setMagfilter(Texture.FTLinearMipmapLinear)
        texture.setAnisotropicDegree(2)

    def load(self):
        """Load textures and shaders."""

    def texturize(self, tile):
        """Apply textures and shaders to the inputted tile."""

###############################################################################
#   MonoTexturer
###############################################################################
class MonoTexturer(TerrainTexturer):
    """Load a single ugly texture onto TerrainTiles."""

    def load(self):
        """single texture"""

        self.ts = TextureStage('ts')
        tex = self.loadTexture("rock.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.monoTexture = tex
    def texturize(self, tile):
        """Apply textures and shaders to the inputted tile."""

        root = tile.getRoot()
        root.setTexture(self.ts, self.monoTexture)
        root.setTexScale(ts, 10, 10)

###############################################################################
#   DetailTexturer
###############################################################################

class DetailTexturer(TerrainTexturer):
    """adds a texture + detail texture to TerrainTiles"""

    def load(self):
        self.ts1 = TextureStage('ts')
        tex = self.loadTexture("snow.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.monoTexture = tex

        self.detailTS = TextureStage('ts2')
        tex = self.loadTexture("Detail4.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.detailTexture = tex
        #self.textureBlendMode = 7
        self.textureBlendMode = self.detailTS.MHeight
        self.detailTS.setMode(self.textureBlendMode)

    def texturize(self, tile):
        """Apply textures and shaders to the inputted tile."""

        root = tile.getRoot()

        root.setTexture(self.ts1, self.monoTexture)
        root.setTexScale(self.ts1, 5, 5)

        root.setTexture(self.detailTS, self.detailTexture)
        root.setTexScale(self.detailTS, 120, 120)


    def setDetailBlendMode(self, num):
        """Set the blending mode of the detail texture."""

        if (not self.detailTexture):
            return
        self.textureBlendMode = num
        #for pos, tile in self.tiles.items():
        #    if tile.detailTS:
        #        tile.detailTS.setMode(self.textureBlendMode)

        self.detailTS.setMode(self.textureBlendMode)

    def incrementDetailBlendMode(self):
        """Set the blending mode of the detail texture."""

        if (not self.detailTexture):
            return
        self.textureBlendMode += 1
        self.setDetailBlendMode(self.textureBlendMode)

    def decrementDetailBlendMode(self):
        """Set the blending mode of the detail texture."""

        if (not self.detailTexture):
            return
        self.textureBlendMode -= 1
        self.setDetailBlendMode(self.textureBlendMode)

###############################################################################
#   ShaderTexturer
###############################################################################
class ShaderTexturer(DetailTexturer):
    """Adds a shader to TerrainTiles.

    The texturer loads and stores several textures and a detail texture for use
    by the shader in texturing the TerrainTiles.

    """
    def load(self):
        """texture + detail texture"""

        DetailTexturer.load(self)
        #self.loadShader2()
        self.loadShader4()

    def loadShader2(self):
        """Textures based on altitude. My own version"""

        self.shader = Shader.load('shaders/stephen2.sha', Shader.SLCg)
        #self.shader = Shader.load('shaders/9.sha', Shader.SLCg)
        #self.shader = Shader.load('shaders/filter-vlight.cg', Shader.SLCg)
        #self.terrain.setShaderInput("casterpos", Vec4(100.0,100.0,100.0,100.0))
        #self.terrain.setShaderInput("light", Vec4(100.0,100.0,100.0,100.0))

        ### texture scaling
        texScale = self.terrain.tileSize / 32 * self.terrain.horizontalScale
        self.texScale = Vec4(texScale, texScale, texScale, 1.0)

        ### Load textures
        self.tex1 = self.loadTexture("dirt.jpg")
        self.tex2 = self.loadTexture("grass.jpg")
        self.tex3 = self.loadTexture("rock.jpg")
        self.tex4 = self.loadTexture("snow.jpg")

        self.ts1 = TextureStage('tex1')
        self.ts2 = TextureStage('tex2')
        self.ts3 = TextureStage('tex3')
        self.ts4 = TextureStage('tex4')


        ### Load the boundries for each texture
        # this is half the blend area between each texture
        blendRadius = self.terrain.maxHeight * 0.11 + 0.5
        transitionHeights = Vec3(self.terrain.maxHeight * self.terrain.waterHeight,
                                 self.terrain.maxHeight * 0.52,
                                 self.terrain.maxHeight * 0.80)

        # regionLimits ( max height, min height, unused/extensible, unused/extensible )
        self.region1 = Vec4(transitionHeights.getX() + blendRadius, -999.0, 0, 0)
        self.region2 = Vec4(transitionHeights.getY() + blendRadius, transitionHeights.getX() - blendRadius, 0, 0)
        self.region3 = Vec4(transitionHeights.getZ() + blendRadius, transitionHeights.getY() - blendRadius, 0, 0)
        self.region4 = Vec4(999.0, transitionHeights.getZ() - blendRadius, 0, 0)

        self.terrain.setShaderInput("region1ColorMap", self.tex1)
        self.terrain.setShaderInput("region2ColorMap", self.tex2)
        self.terrain.setShaderInput("region3ColorMap", self.tex3)
        self.terrain.setShaderInput("region4ColorMap", self.tex4)
        self.terrain.setShaderInput("detailTexture", self.detailTexture)
        self.terrain.setShaderInput("region1Limits", self.region1)
        self.terrain.setShaderInput("region2Limits", self.region2)
        self.terrain.setShaderInput("region3Limits", self.region3)
        self.terrain.setShaderInput("region4Limits", self.region4)
        self.terrain.setShaderInput('tscale', self.texScale)

        self.terrain.setShader(self.shader)

    def loadShader4(self):
        """Textures based on altitude and slope. My own version. Normal data appears broken."""

        
        #self.shader = Shader.load('shaders/9.sha', Shader.SLCg)
        #self.shader = Shader.load('shaders/filter-vlight.cg', Shader.SLCg)
        #self.terrain.setShaderInput("casterpos", Vec4(100.0,100.0,100.0,100.0))
        #self.terrain.setShaderInput("light", Vec4(100.0,100.0,100.0,100.0))

        ### texture scaling
        texScale = self.terrain.tileSize / 32 * self.terrain.horizontalScale
        self.texScale = Vec4(texScale, texScale, texScale, 1.0)

        ### Load textures
        self.tex1 = self.loadTexture("dirt.jpg")
        self.tex2 = self.loadTexture("grass.jpg")
        self.tex3 = self.loadTexture("rock.jpg")
        self.tex4 = self.loadTexture("snow.jpg")

        self.ts1 = TextureStage('tex1')
        self.ts2 = TextureStage('tex2')
        self.ts3 = TextureStage('tex3')
        self.ts4 = TextureStage('tex4')


        ### Load the boundries for each texture
        # this is half the blend area between each texture
        blendRadius = self.terrain.maxHeight * 0.11 + 0.5
        transitionHeights = Vec3(self.terrain.maxHeight * self.terrain.waterHeight,
                                 self.terrain.maxHeight * 0.56,
                                 self.terrain.maxHeight * 0.80)

        # regionLimits ( max height, min height, slope max, slope min )
        sg = TerrainShaderGenerator(self.terrain)

        sg.addTexture(self.tex1)
        sg.addRegionToTex(Vec4(transitionHeights.getX() + blendRadius, -999.0, 1, 0))

        sg.addTexture(self.tex2)
        sg.addRegionToTex(Vec4(transitionHeights.getY() + blendRadius, transitionHeights.getX() - blendRadius, 0.30, 0))

        sg.addTexture(self.tex3)
        sg.addRegionToTex(Vec4(transitionHeights.getY() + blendRadius, transitionHeights.getX()- blendRadius, 1.0, 0.15))
        sg.addRegionToTex(Vec4(transitionHeights.getZ() + blendRadius, transitionHeights.getY() - blendRadius, 1.0, 0))

        sg.addTexture(self.tex4)
        sg.addRegionToTex(Vec4(999.0, transitionHeights.getZ() - blendRadius, 1.0, 0))
        sg.createShader()

        self.terrain.setShaderInput("detailTexture", self.detailTexture)
        self.terrain.setShaderInput('tscale', self.texScale)

        self.shader = Shader.load('shaders/stephen5.sha', Shader.SLCg)
        self.terrain.setShader(self.shader)

    def texturize(self, tile):
        """Apply textures and shaders to the inputted tile."""
        root = tile.getRoot()

        #root.setTexture(self.detailTS, self.detailTexture)
        #root.setTexScale(self.detailTS, 120, 120)

        # enable use of the two separate tagged render states for our two cameras
        #root.setTag('Normal', 'True')
        #root.setTag('Clipped', 'True')
        root.setTexture(self.ts1, self.tex1)
        root.setTexture(self.ts2, self.tex2)
        root.setTexture(self.ts3, self.tex3)
        root.setTexture(self.ts4, self.tex4)
        root.setTexture(self.detailTS, self.detailTexture)
        root.setTexScale(self.detailTS, 120, 120)

