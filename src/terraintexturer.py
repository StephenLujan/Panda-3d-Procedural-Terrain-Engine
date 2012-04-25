"""
terraintexturer.py: This file contains the TerrainTextur class.

The TerrainTexturer handles all textures and or shaders on the terrain and is
generally responsible for the appearance of the terrain.
"""
__author__ = "Stephen Lujan"
__date__ = "$Dec 15, 2010 2:14:33 AM$"


from config import *
from panda3d.core import Shader
from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import Texture
from pandac.PandaModules import TextureStage
from pandac.PandaModules import Vec3
from pandac.PandaModules import Vec4
from fullterrainshadergenerator import *
from bakedterrainshadergenerator import *
from terraintexturemap import *

###############################################################################
#   TerrainTexturer
###############################################################################

class TerrainTexturer():
    """Virtual Class"""

    def __init__(self, terrain):
        """initialize"""

        logging.info( "initializing terrain texturer...")
        self.terrain = terrain
        self.load()

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

    def apply(self, input):
        """Apply textures and shaders to the input."""

    def indexToHeight(self, input):
        """Maps a decimal [0.0, 1.0] to [waterHeight, maxHeight]"""
        wh = self.terrain.waterHeight * self.terrain.maxHeight
        return input * (self.terrain.maxHeight - wh) + wh

    def heightToIndex(self, input):
        """Maps the height above sea level to a decimal index."""
        wh = self.terrain.waterHeight * self.terrain.maxHeight
        return (input - wh) / (self.terrain.maxHeight - wh)


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
    def apply(self, input):
        """Apply textures and shaders to the input."""

        input.setTexture(self.ts, self.monoTexture)
        input.setTexScale(self.ts, 10, 10)

###############################################################################
#   DetailTexturer
###############################################################################

class DetailTexturer(TerrainTexturer):
    """adds a texture + detail texture to TerrainTiles"""

    def load(self):
        self.ts1 = TextureStage('ts2')
        tex = self.loadTexture("snow.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.monoTexture = tex

        self.loadDetail()

    def loadDetail(self):
        self.detailTS = TextureStage('ts')
        tex = self.loadTexture("Detail_COLOR.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.detailTexture = tex
        self.textureBlendMode = self.detailTS.MHeight
        self.detailTS.setMode(self.textureBlendMode)

    def apply(self, input):
        """Apply textures and shaders to the input."""

        input.setTexture(self.ts1, self.monoTexture)
        input.setTexScale(self.ts1, 5, 5)

        input.setTexture(self.detailTS, self.detailTexture)
        input.setTexScale(self.detailTS, 120, 120)


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
class ShaderTexturer(TerrainTexturer):
    """Adds a shader to TerrainTiles.

    The texturer loads and stores several textures and a detail texture for use
    by the shader in texturing the TerrainTiles.

    """
    def load(self):
        """texture + detail texture"""

        self.loadShader()

    def loadShader(self):
        """Textures based on altitude and slope."""

        logging.info( "loading textures...")
        ### texture scaling
        texScale = self.terrain.tileSize / 32 * self.terrain.horizontalScale
        self.texScale = Vec4(texScale, texScale, texScale, 1.0)

        ### Load textures
        self.normalMap = self.loadTexture("Detail_NRM.png")
        self.displacementMap = self.loadTexture("Detail_DISP.png")
        self.testOn = False
        self.detailTex = self.loadTexture("Detail_COLOR.png")
        self.detailTex2 = self.loadTexture("Detail_COLOR2.png")
        self.tex1 = self.loadTexture("dirt.jpg")
        self.tex2 = self.loadTexture("grass.jpg")
        self.tex3 = self.loadTexture("rock.jpg")
        self.tex4 = self.loadTexture("snow.jpg")

        self.normalTS = TextureStage('normalMap')
        #self.normalTS2 = TextureStage('normalMap2')
        self.detailTS = TextureStage('detailMap')
        self.ts1 = TextureStage('textures')

        ### Load the boundries for each texture
        # regionLimits ( min height, max height, min slope, max slope )

        self.textureMapper = TextureMapper(self.terrain)

        self.textureMapper.addTexture(self.tex1)
        self.textureMapper.addRegionToTex(Vec4(-9999.0, self.indexToHeight(0.1), -0.001, 1.001))

        self.textureMapper.addTexture(self.tex2)
        self.textureMapper.addRegionToTex(Vec4(self.indexToHeight(-0.15), self.indexToHeight(0.75), -0.001, 0.30))

        self.textureMapper.addTexture(self.tex3)
        self.textureMapper.addRegionToTex(Vec4(self.indexToHeight(0.1), self.indexToHeight(0.95), 0.10, 1.001))
        #second region forces tex 2 and 4 to blend a bit at their boundries regardless of slope
        self.textureMapper.addRegionToTex(Vec4(self.indexToHeight(0.4), self.indexToHeight(0.9), -0.001, 1.001))

        self.textureMapper.addTexture(self.tex4)
        self.textureMapper.addRegionToTex(Vec4(self.indexToHeight(0.72), 9999.0, -0.001, 1.001))

        logging.info( "intializing terrain shader generator...")
        file = 'shaders/terrain.sha'
        if SAVED_TEXTURE_MAPS:
            self.shaderGenerator = BakedTerrainShaderGenerator(self.terrain, self, self.textureMapper)
            file = 'shaders/bakedTerrain.sha'
        else:
            self.shaderGenerator = FullTerrainShaderGenerator(self.terrain, self,  self.textureMapper)
            file = 'shaders/fullTerrain.sha'
        logging.info( "terrain shader generator initialized...")

        if RUNTYPE == 'python':
            self.shaderGenerator.saveShader(file)
            self.shader = Shader.load(file, Shader.SLCg)
        else:
            self.shader = Shader.make(self.shaderGenerator.createShader(), Shader.SLCg);

        self.terrain.setShaderInput("normalMap", self.normalMap)
        self.terrain.setShaderInput("displacementMap", self.displacementMap)
        self.terrain.setShaderInput("detailTex", self.detailTex)
        self.terrain.setShaderInput('tscale', self.texScale)
        self.terrain.setShaderInput("fogColor", Vec4(1.0, 1.0, 1.0, 1.0))
        self.terrain.setShaderInput("camPos", base.camera.getPos())

    def apply(self, input):
        """Apply textures and shaders to the input."""

        # we can just leave most shader inputs on top of terrain

        ### apply textures
        #input.setTexture(self.ts1, self.tex1)
        #input.setTexture(self.ts1, self.tex2)
        #input.setTexture(self.ts1, self.tex3)
        #input.setTexture(self.ts1, self.tex4)
        #input.setTexture(self.detailTS, self.detailTex)
        #input.setTexScale(self.detailTS, 10, 10)

        ### apply shader
        #input.setShaderInput("normalMap", self.normalMap)
        #input.setShaderInput("detailTex", self.detailTex)
        #input.setShaderInput('tscale', self.texScale)
        #input.setShaderInput("fogColor", Vec4(1.0,1.0,1.0,1.0))
        #input.setShaderInput("camPos", base.camera.getPos())

        input.setShader(self.shader)

    def test(self):
        # nothing I want to test here right now
        return