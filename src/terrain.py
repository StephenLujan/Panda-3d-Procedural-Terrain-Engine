###
# This file contains the terrain engine for panda 3d.

__author__ = "Stephen"
__date__ = "$Oct 27, 2010 4:47:05 AM$"

import math

from panda3d.core import BitMask32
from panda3d.core import CollisionHandlerQueue
from panda3d.core import CollisionNode
from panda3d.core import CollisionRay
from panda3d.core import CollisionTraverser
from panda3d.core import PNMImage
from panda3d.core import PerlinNoise2
from panda3d.core import Shader
from panda3d.core import StackedPerlinNoise2
from pandac.PandaModules import Filename
from pandac.PandaModules import GeoMipTerrain
from pandac.PandaModules import NodePath
from pandac.PandaModules import PandaNode
from pandac.PandaModules import Point3
from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import Texture
from pandac.PandaModules import TextureStage
from pandac.PandaModules import Vec2
from pandac.PandaModules import Vec3
from pandac.PandaModules import Vec4

###############################################################################
#   HeightMapTile
###############################################################################

class HeightMapTile(GeoMipTerrain):

    def __init__(self, terrain, x, y):
        """Important settings are used directly from the terrain.
        This allows for easier setting changes, and reduces memory overhead.
        x and y parameters give the appropriate world coordinates of this tile.

        """

        self.terrain = terrain
        self.xOffset = x
        self.yOffset = y


        name = terrain.name + "X" + str(x) + "Y" + str(y)
        GeoMipTerrain.__init__(self, name=terrain.name)

        self.mapName = "heightmaps/" + name + ".png"
        self.image = PNMImage()

        self.getRoot().setPos(x, y, 0)
        GeoMipTerrain.setFocalPoint(self, terrain.focus)
        #GeoMipTerrain.setMinLevel(self,1)


        #self.generateNoiseObjects()
        #self.make()

    def update(self, dummy):
        """Updates the GeoMip to use the correct LOD on each block."""

        GeoMipTerrain.update(self)

    def updateTask(self, task):
        """Updates the GeoMip to use the correct LOD on each block."""

        self.update(task)
        return task.again

    def setHeightField(self, filename):
        """Set the GeoMip heightfield from a heightmap image."""

        GeoMipTerrain.setHeightfield(self, filename)

    def setHeight(self):
        """Set the heightfield to the the image file or generate a new one."""

        if (self.image.getXSize() < 1):
            self.image.read(Filename(self.mapName))
            if (self.image.getXSize() < 1):
                self.makeHeightMap()
                self.image.read(Filename(self.mapName))
        self.setHeightField(Filename(self.mapName))

    def makeHeightMap(self):
        """Generate a new heightmap image to use."""

        self.image = PNMImage(self.terrain.heightMapSize, self.terrain.heightMapSize)
        self.image.makeGrayscale()
        self.image.setNumChannels(1)
        self.image.setMaxval(65535)

        #        max = -9999.0
        #        min = 9999.0
        #        height = 0

            # return the minimum and maximum, useful to normalize the heightmap
        #        for x in range(self.xOffset, self.xOffset + self.image.getXSize()):
        #            for y in range(self.yOffset, self.yOffset + self.image.getYSize()):
        #                height = self.terrain.getHeight(x, y)
        #                if height < min:
        #                    min = height
        #                if height > max:
        #                    max = height

        #normalMax = -9999.0
        #normalMax = 9999.0

        #print "generating heightmap for offsets: ",self.xOffset,self.yOffset

        for x in range(self.image.getXSize()):
            for y in range(self.image.getYSize()):
                height = self.terrain.getHeight(x + self.xOffset, y + self.yOffset)
                #normalize height
                #height = (height - min) / (max-min)
                #feed pixel into image
                #why is it necessary to invert the y axis I wonder?
                self.image.setGray(x, self.image.getYSize()-1-y, height)
                #this is just a test
                #if height < normalMin:
                #    normalMin = height
                #if height > normalMax:
                #    normalMax = height

        self.postProcessImage()

        #print ("Prenomalized max = " + str(max))
        #print ("Prenomalized min = " + str(min))
        self.image.write(Filename(self.mapName))

    def postProcessImage(self):
        """Perform filters and manipulations on the heightmap image."""

        #self.image.gaussianFilter()

    def wireframe(self):
        self.getRoot().setRenderModeWireframe()

    def make(self):
        """Build a finished renderable heightMap."""

        #self.generateNoiseObjects()
        self.makeHeightMap()
        self.setHeight()
        #self.getRoot().setSz(self.maxHeight)
        self.generate()

###############################################################################
#   TerrainTile
###############################################################################

class TerrainTile(HeightMapTile):
    """The TerrainTile is a heightmap tile that textures and or shaders.
    Texture storage and loading should be moved to an outside class.

    """

    def __init__(self, terrain, x, y):
        """Important settings are used directly from the terrain.
        This allows for easier setting changes, and reduces memory overhead.
        x and y parameters give the appropriate world coordinates of this tile.

        """

        HeightMapTile.__init__(self, terrain, x, y)

        self.textureBlendMode = 7
        self.detailTexture = 0

    def setMonoTexture(self):
        """single texture"""

        root = self.getRoot()
        ts = TextureStage('ts')
        tex = loader.loadTexture("textures/rock.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        root.setTexture(ts, tex)
        root.setTexScale(ts, 10, 10)

    def setDetailBlendMode(self, num):
        """Set the blending mode of the detail texture."""

        if (not self.detailTexture):
            return
        self.textureBlendMode = num
        self.detailTexture.setMode(self.textureBlendMode)

    def incrementDetailBlendMode(self):
        """Set the blending mode of the detail texture."""

        if (not self.detailTexture):
            return
        self.textureBlendMode += 1
        self.detailTexture.setMode(self.textureBlendMode)

    def decrementDetailBlendMode(self):
        """Set the blending mode of the detail texture."""

        if (not self.detailTexture):
            return
        self.textureBlendMode -= 1
        self.detailTexture.setMode(self.textureBlendMode)

    def setDetailTexture(self):
        """texture + detail texture"""

        root = self.getRoot()

        ts = TextureStage('ts')
        tex = loader.loadTexture("textures/snow.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        root.setTexture(ts, tex)
        root.setTexScale(ts, 5, 5)

        self.detailTexture = TextureStage('ts2')
        tex = loader.loadTexture("textures/Detail.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        root.setTexture(self.detailTexture, tex)
        self.setDetailBlendMode(2)
        root.setTexScale(self.detailTexture, 120, 120)

    def setShader2(self):
        """Textures based on altitude. My own version"""

        root = self.getRoot()

        self.myShader = Shader.load('shaders/stephen2.sha', Shader.SLCg)
        root.setShader(self.myShader)

        # texture scaling
        texScale = self.terrain.tileSize/32
        root.setShaderInput('tscale', Vec4(texScale, texScale, texScale, 1.0))


        # this is half the blend area between each texture
        blendRadius = self.terrain.maxHeight * 0.11 + 0.5
        transitionHeights = Vec3(self.terrain.maxHeight * self.terrain.waterHeight,
                                 self.terrain.maxHeight * 0.52,
                                 self.terrain.maxHeight * 0.80)

        # This is the current shader input format. The unused parameters are
        # for easy extensibility.
        #   regionLimits ( max height, min height, unused, unused)
        root.setShaderInput("region1Limits", Vec4(transitionHeights.getX() + blendRadius, -999.0, 0, 0))
        root.setShaderInput("region2Limits", Vec4(transitionHeights.getY() + blendRadius, transitionHeights.getX() - blendRadius, 0, 0))
        root.setShaderInput("region3Limits", Vec4(transitionHeights.getZ() + blendRadius, transitionHeights.getY() - blendRadius, 0, 0))
        root.setShaderInput("region4Limits", Vec4(999.0, transitionHeights.getZ() - blendRadius, 0, 0))

        #self.tex0 = loader.loadTexture(self.mapName)
        self.tex1 = loader.loadTexture("textures/dirt.jpg")
        #self.tex1.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex1.setMagfilter(Texture.FTLinear)
        self.tex2 = loader.loadTexture("textures/grass.jpg")
        #self.tex2.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex2.setMagfilter(Texture.FTLinear)
        self.tex3 = loader.loadTexture("textures/rock.jpg")
        #self.tex3.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex3.setMagfilter(Texture.FTLinear)
        self.tex4 = loader.loadTexture("textures/snow.jpg")
        #self.tex4.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex4.setMagfilter(Texture.FTLinear)

        ts = TextureStage('tex1')	# stage 0
        root.setTexture(ts, self.tex1)
        ts = TextureStage('tex2')	# stage 1
        root.setTexture(ts, self.tex2)
        ts = TextureStage('tex3')	# stage 2
        root.setTexture(ts, self.tex3)
        ts = TextureStage('tex4')	# stage 3
        root.setTexture(ts, self.tex4)

        root.setShaderInput("region1ColorMap", self.tex1)
        root.setShaderInput("region2ColorMap", self.tex2)
        root.setShaderInput("region3ColorMap", self.tex3)
        root.setShaderInput("region4ColorMap", self.tex4)

        # enable use of the two separate tagged render states for our two cameras
        root.setTag('Normal', 'True')
        root.setTag('Clipped', 'True')

        #self.shaderAttribute = ShaderAttrib.make( )
        #self.shaderAttribute = self.shaderAttribute.setShader(
        #loader.loadShader('shaders/stephen.sha'))


    def setShader4(self):
        """Textures based on altitude and slope. My own version. Normal data appears broken."""

        root = self.getRoot()

        self.myShader = Shader.load('shaders/stephen4.sha', Shader.SLCg)
        root.setShader(self.myShader)

        #self.tex0 = loader.loadTexture(self.mapName)
        self.tex1 = loader.loadTexture("textures/dirt.jpg")
        #self.tex1.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex1.setMagfilter(Texture.FTLinear)
        self.tex2 = loader.loadTexture("textures/grass.jpg")
        #self.tex2.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex2.setMagfilter(Texture.FTLinear)
        self.tex3 = loader.loadTexture("textures/rock.jpg")
        #self.tex3.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex3.setMagfilter(Texture.FTLinear)
        self.tex4 = loader.loadTexture("textures/snow.jpg")
        #self.tex4.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex4.setMagfilter(Texture.FTLinear)

        ts = TextureStage('tex1')	# stage 0
        root.setTexture(ts, self.tex1)
        ts = TextureStage('tex2')	# stage 1
        root.setTexture(ts, self.tex2)
        ts = TextureStage('tex3')	# stage 2
        root.setTexture(ts, self.tex3)
        ts = TextureStage('tex4')	# stage 3
        root.setTexture(ts, self.tex4)

        
        root.setShaderInput("region1ColorMap", self.tex1)
        root.setShaderInput("region2ColorMap", self.tex2)
        root.setShaderInput("region3ColorMap", self.tex3)
        root.setShaderInput("region4ColorMap", self.tex4)

        root.setShaderInput('tscale', Vec4(16.0, 16.0, 16.0, 1.0))	# texture scaling

        blendArea = self.maxHeight * 0.11 + 0.5

        # This is the current shader input format.
        # Limits : height max, height min, slope max, slope min
        root.setShaderInput("region1Limits", Vec4(12 + blendArea, -999.0, 0.6, 0.0))
        root.setShaderInput("region2Limits", Vec4(self.maxHeight * 0.65, 10, 0.6, 0.0))
        root.setShaderInput("region3Limits", Vec4(self.maxHeight * 0.8 + blendArea, 12.0, 1.0, 0.3))
        root.setShaderInput("region4Limits", Vec4(999.0, self.maxHeight * 0.8 - blendArea, 1.0, 0.0))

        # enable use of the two separate tagged render states for our two cameras
        # This is not working fully at the moment
        root.setTag('Normal', 'True')
        root.setTag('Clipped', 'True')
        #self.shaderAttribute = ShaderAttrib.make( )
        #self.shaderAttribute = self.shaderAttribute.setShader(
        #loader.loadShader('shaders/stephen2.sha'))

    def setMultiTexture(self):
        """Set up the appropriate shader for multi texture terrain."""
        self.setShader2()

    def make(self):

        self.setMultiTexture()
        HeightMapTile.make(self)
        #self.setMultiTexture()

###############################################################################
#   Terrain
###############################################################################

class Terrain(NodePath):
    def __init__(self, name, focus):
        NodePath.__init__(self, name)

        self.name = name

        ### tile physical properties
        self.maxHeight = 200
        self.heightMapSize = 129
        self.tileSize = self.heightMapSize - 1
        self.consistency = 1000
        self.smoothness = 100
        self.waterHeight = 0.3
        # for realism the flatHeight should be at or very close to waterHeight
        self.flatHeight = self.waterHeight

        ### rendering properties
        self.blockSize = 32
        self.near = 15
        self.far = 80

        ### tile generation
        # Don't show untiled terrain below this distance etc.
        self.maxViewRange = 400
        # Add half the tile size because distance is checked from the center,
        # not from the closest edge.
        self.minTileDistance = self.maxViewRange + self.tileSize/2
        # make larger to avoid excess loading when milling about a small area
        # make smaller to shrink some overhead
        self.maxTileDistance = self.minTileDistance * 1.5
        self.focus = focus

        self.generateNoiseObjects()

        self.tiles = {}

        self.makeNewTiles(focus.getX(), focus.getY())

        self.setSz(self.maxHeight)
        self.setupElevationRay()

    def updateTask(self, task):
        """This task adds and removes terrain tiles as needed.
        It also updates each tile, which updates the LOD.

        """

        for pos, tile in self.tiles.items():
            tile.update(task)
            
        self.makeNewTiles(self.focus.getX(), self.focus.getY())
        self.removeOldTiles(self.focus.getX(), self.focus.getY())
        return task.again

    def makeNewTiles(self, x, y):
        """generate terrain tiles as needed."""

        xstart = (int(x) / self.tileSize) * self.tileSize
        ystart = (int(y) / self.tileSize) * self.tileSize
        radius = (self.minTileDistance / self.tileSize + 2) * self.tileSize

        #print xstart, ystart, radius

        for checkX in range (xstart - radius, xstart + radius, self.tileSize):
            for checkY in range (ystart - radius, ystart + radius, self.tileSize):
                deltaX = x - (checkX + self.tileSize * 0.5)
                deltaY = y - (checkY + self.tileSize * 0.5)
                if math.sqrt(deltaX * deltaX + deltaY * deltaY) \
                   < self.minTileDistance:
                    if not Vec2(checkX, checkY) in self.tiles:
                        tile = self.generateTile(checkX, checkY)
                        print "tile generated at", checkX, checkY

    def removeOldTiles(self, x, y):
        """todo"""

    def generateTile(self, x, y):
        """Creates a terrain tile at the input coordinates."""

        tile = TerrainTile(self, x, y)
        tile.make()
        #np = self.attachNewNode("tileNode")
        #np.reparentTo(self)
        #tile.getRoot().reparentTo(np)
        #self.tiles.append(np)
        tile.getRoot().reparentTo(self)
        self.tiles[Vec2(x, y)] = tile
        return tile


    def generateNoiseObjects(self, seed=0):
        """Create perlin noise."""

        # where perlin 1 is low terrain will be mostly low and flat
        # where it is high terrain will be higher and slopes will be exagerrated
        # increase perlin1 to create larger areas of geographic consistency
        # increasing it too much on a small map may not work due normalization
        #        self.perlin1 = StackedPerlinNoise2()
        #        stackSpread = 1.2
        #        perlin1Course = PerlinNoise2( self.heightMapSize, self.heightMapSize  )
        #        perlin1Course.setScale( self.consistency *stackSpread)
        #        self.perlin1.addLevel( perlin1Course, stackSpread)
        #        perlin1Fine = PerlinNoise2( self.heightMapSize, self.heightMapSize)
        #        perlin1Fine.setScale( self.consistency / stackSpread)
        #        self.perlin1.addLevel( perlin1Fine, 1 / stackSpread)
        self.perlin1 = PerlinNoise2()
        self.perlin1.setScale(self.consistency)

        # perlin2 creates the noticeable noise in the terrain
        # without perlin2 everything would look unnaturally smooth and regular
        # increase perlin2 to make the terrain smoother
        self.perlin2 = StackedPerlinNoise2()
        frequencySpread = 3.0
        amplitudeSpread = 3.2
        perlin2a = PerlinNoise2()
        perlin2a.setScale(self.smoothness)
        self.perlin2.addLevel(perlin2a)
        perlin2b = PerlinNoise2()
        perlin2b.setScale(self.smoothness / frequencySpread)
        self.perlin2.addLevel(perlin2b, 1 / amplitudeSpread)
        perlin2c = PerlinNoise2()
        perlin2c.setScale(self.smoothness / (frequencySpread*frequencySpread))
        self.perlin2.addLevel(perlin2c, 1 / (amplitudeSpread*amplitudeSpread))
        perlin2d = PerlinNoise2()
        perlin2d.setScale(self.smoothness / (math.pow(frequencySpread,3)))
        self.perlin2.addLevel(perlin2d, 1 / (math.pow(amplitudeSpread,3)))
        perlin2e = PerlinNoise2()
        perlin2e.setScale(self.smoothness / (math.pow(frequencySpread,4)))
        self.perlin2.addLevel(perlin2e, 1 / (math.pow(amplitudeSpread,4)))
        #        self.perlin2 = PerlinNoise2( self.heightMapSize, self.heightMapSize)
        #        self.perlin2.setScale( self.smoothness )

    def getHeight(self, x, y):
        """Returns the height at the specified terrain coordinates.
        The values returned should be between 0 and 1 and use the full range.
        Heights should be the smoothest and flatest at flatHeight.

        """

        return ((self.perlin1(x, y) + 1 - self.flatHeight) / 4 + \
                ((self.perlin1(x, y) + 1 - self.flatHeight) * \
                (self.perlin2(x, y) + 1 - self.flatHeight)) / 8) \
                + self.flatHeight

    def getElevation(self, x, y):
        """Returns the height of the terrain at the input world coordinates."""

        return self.getHeight(x, y) * self.getSz()

        #        self.elevationRay.setOrigin(x,y,1000)
        #        self.cTrav.traverse(render)
        #
        #        entries = []
        #        for i in range(self.elevationHandler.getNumEntries()):
        #            entry = self.elevationHandler.getEntry(i)
        #            entries.append(entry)
        #        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
        #                                     x.getSurfacePoint(render).getZ()))
        #        if (len(entries)>0):#and (entries[0].getIntoNode().getName() == "terrain"):
        #            print "success!"
        #            return entries[0].getSurfacePoint(render).getZ()
        #        else:
        #            print "failure!"
        #            return self.getHeight(x, y) * self.getSz()

        #for pos, tile in self.tiles.items():
        #    if x > tile.getRoot().getX() and x < tile.getRoot().getSx() \
        #       * self.tileSize + tile.getRoot().getX():
        #        if y > tile.getRoot().getY() and y < tile.getRoot().getSy() \
        #           * self.tileSize + tile.getRoot().getY():
        #            return tile.getElevation(x- tile.getRoot().getX(),
        #                                y- tile.getRoot().getY()) * self.getSz()

        print "getElevation() failure!"


    def setupElevationRay(self):
        """ Doesn't appear to work. """

        self.elevationRay = CollisionRay()
        self.elevationRay.setOrigin(50, 50, 1000)
        self.elevationRay.setDirection(0, 0, -1)
        self.elevationCol = CollisionNode('elevationRay')
        self.elevationCol.addSolid(self.elevationRay)
        self.elevationCol.setFromCollideMask(BitMask32.bit(0))
        self.elevationCol.setIntoCollideMask(BitMask32.allOff())
        self.elevationColNp = render.attachNewNode(self.elevationCol)
        self.elevationHandler = CollisionHandlerQueue()
        self.cTrav = CollisionTraverser()
        self.cTrav.addCollider(self.elevationColNp, self.elevationHandler)



###############################################################################
#   TerrainTexturer
###############################################################################

class TerrainTexturer():
    """Not yet complete or implemented."""
    
    def LoadMonoTexture(self):
        """single texture"""

        tex = loader.loadTexture("textures/rock.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.monoTexture = tex

    def setDetailBlendMode(self, num):
        """Set the blending mode of the detail texture."""

        if (not self.detailTexture):
            return
        self.textureBlendMode = num

        for pos, tile in self.tiles.items():
            if tile.detailTexture:
                tile.detailTexture.setMode(self.textureBlendMode)

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

    def LoadDetailTexture(self):
        """texture + detail texture"""

        tex = loader.loadTexture("textures/snow.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)

        self.detailTexture = TextureStage('ts2')
        tex = loader.loadTexture("textures/Detail.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.textureBlendMode = 7

    def LoadMultiTexture(self):

        #self.tex0 = loader.loadTexture(self.mapName)
        self.tex1 = loader.loadTexture("textures/dirt.jpg")
        #self.tex1.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex1.setMagfilter(Texture.FTLinear)
        self.tex2 = loader.loadTexture("textures/grass.jpg")
        #self.tex2.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex2.setMagfilter(Texture.FTLinear)
        self.tex3 = loader.loadTexture("textures/rock.jpg")
        #self.tex3.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex3.setMagfilter(Texture.FTLinear)
        self.tex4 = loader.loadTexture("textures/snow.jpg")
        #self.tex4.setMinfilter(Texture.FTNearestMipmapLinear)
        #self.tex4.setMagfilter(Texture.FTLinear)

        #root.setShaderInput( "tex0", self.tex0 )
        root.setShaderInput("region1ColorMap", self.tex1)
        root.setShaderInput("region2ColorMap", self.tex2)
        root.setShaderInput("region3ColorMap", self.tex3)
        root.setShaderInput("region4ColorMap", self.tex4)
        

    def LoadShader2(self):
        """Textures based on altitude. My own version"""

        self.shader2 = Shader.load('shaders/stephen2.sha', Shader.SLCg)
        setShaderInput('tscale', Vec4(16.0, 16.0, 16.0, 1.0))	# texture scaling

        blendArea = self.terrain.maxHeight * 0.11 + 0.5 #actually half the blend area
        transitionHeights = Vec3(12.0 + blendArea / 2, self.terrain.maxHeight * 0.52, self.terrain.maxHeight * 0.82)

        # regionLimits ( max height, min height, unused/extensible, unused/extensible )
        setShaderInput("region1Limits", Vec4(transitionHeights.getX() + blendArea, -999.0, 0, 0))
        setShaderInput("region2Limits", Vec4(transitionHeights.getY() + blendArea, transitionHeights.getX() - blendArea, 0, 0))
        setShaderInput("region3Limits", Vec4(transitionHeights.getZ() + blendArea, transitionHeights.getY() - blendArea, 0, 0))
        setShaderInput("region4Limits", Vec4(999.0, transitionHeights.getZ() - blendArea, 0, 0))

    def LoadShader4(self):
        """Textures based on altitude and slope. My own version. Normal data appears broken."""


        self.myShader = Shader.load('shaders/stephen4.sha', Shader.SLCg)
        root.setShader(self.myShader)

        #root.setShaderInput( "tex0", self.tex0 )
        root.setShaderInput("region1ColorMap", self.tex1)
        root.setShaderInput("region2ColorMap", self.tex2)
        root.setShaderInput("region3ColorMap", self.tex3)
        root.setShaderInput("region4ColorMap", self.tex4)

        root.setShaderInput('tscale', Vec4(16.0, 16.0, 16.0, 1.0))	# texture scaling

        blendArea = self.maxHeight * 0.11 + 0.5
        # Limits (height max, height min, slope max, slope min)
        root.setShaderInput("region1Limits", Vec4(12 + blendArea, -999.0, 0.6, 0.0))
        root.setShaderInput("region2Limits", Vec4(self.maxHeight * 0.65, 10, 0.6, 0.0))
        root.setShaderInput("region3Limits", Vec4(self.maxHeight * 0.8 + blendArea, 12.0, 1.0, 0.3))
        root.setShaderInput("region4Limits", Vec4(999.0, self.maxHeight * 0.8 - blendArea, 1.0, 0.0))

        # enable use of the two separate tagged render states for our two cameras
        root.setTag('Normal', 'True')
        root.setTag('Clipped', 'True')
        #self.shaderAttribute = ShaderAttrib.make( )
        #self.shaderAttribute = self.shaderAttribute.setShader(
        #loader.loadShader('shaders/stephen2.sha'))

    def setMultiTexture(self):
        """Set up the appropriate shader for multi texture terrain."""
        self.setShader2()

    def texturize(tile):
        """Apply textures and shaders to the inputted tile."""