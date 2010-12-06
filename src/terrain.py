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
from direct.task.Task import Task
from operator import itemgetter

###############################################################################
#   TerrainTile
###############################################################################

class TerrainTile(GeoMipTerrain):

    def __init__(self, terrain, x, y):
        """Important settings are used directly from the terrain.
        This allows for easier setting changes, and reduces memory overhead.
        x and y parameters give the appropriate world coordinates of this tile.

        """

        self.terrain = terrain
        self.xOffset = x
        self.yOffset = y


        name = "ID" + str(terrain.id) + "X" + str(x) + "Y" + str(y)
        GeoMipTerrain.__init__(self, name=terrain.name)

        self.mapName = "heightmaps/" + name + ".png"
        self.image = PNMImage()

        self.getRoot().setPos(x, y, 0)
        GeoMipTerrain.setFocalPoint(self, terrain.focus)
        if self.terrain.bruteForce:
            GeoMipTerrain.setMinLevel(self,1)
            GeoMipTerrain.setBruteforce(self, True)
        else:
            self.setBorderStitching(1)
        self.setNear(self.terrain.near)
        self.setFar(self.terrain.far)
        
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
#   Terrain
###############################################################################

class Terrain(NodePath):
    def __init__(self, name, focus, id = 321):
        NodePath.__init__(self, name)

        self.name = name

        ### tile physical properties
        self.maxHeight = 200
        self.tileSize = 128
        self.heightMapSize = self.tileSize + 1
        self.consistency = 1000 # how quickly altitude and roughness shift
        self.smoothness = 150 # the overall smoothness/roughness of the terrain
        self.waterHeight = 0.3 # out of a max of 1.0
        # for realism the flatHeight should be at or very close to waterHeight
        self.flatHeight = self.waterHeight+0.03
        self.id = id

        ### rendering properties
        self.bruteForce = True
        #alterblocksize of terrain tiles based on distance
        #this works well with bruteforce terrain.
        self.lodBlockSize = self.bruteForce
        self.blockSize = 16
        self.midBlockSize = 64
        self.farBlockSize = 128
        self.near = 40
        self.far = 100
        self.wireFrame = 0
        self.texturer = ShaderTexturer(self)
        #self.texturer = DetailTexturer(self)
        self.texturer.load()

        ### tile generation
        # Don't show untiled terrain below this distance etc.
        self.maxViewRange = 1000
        # Add half the tile size because distance is checked from the center,
        # not from the closest edge.
        self.minTileDistance = self.maxViewRange + self.tileSize/2
        # make larger to avoid excess loading when milling about a small area
        # make smaller to shrink some overhead
        self.maxTileDistance = self.minTileDistance * 1.3 + self.tileSize
        self.focus = focus

        self.generateNoiseObjects()

        self.tiles = {}

        #self.makeNewTiles(focus.getX(), focus.getY())

        self.setSz(self.maxHeight)
        self.setupElevationRay()

        #Add tasks to keep updating the terrain
        #def setupTaskChain(self, chainName, numThreads=None, tickClock=None,
        #       threadPriority=None, frameBudget=None, timeslicePriority=None)

        taskMgr.setupTaskChain('updateTilesChain', numThreads=1, tickClock=0,
                               threadPriority=0, frameBudget=0.1,
                               frameSync=False, timeslicePriority=True)
        taskMgr.add(self.updateTask, "updateTiles", taskChain='updateTilesChain',
                    sort=99, priority=0)

        taskMgr.setupTaskChain('loadTilesChain', numThreads=2, tickClock=0,
                               threadPriority=1, frameBudget=0.2,
                               frameSync=False, timeslicePriority=True)
        taskMgr.add(self.tileBuilderTask, "loadTiles", taskChain='loadTilesChain',
                    sort=99, priority=0)

        if self.bruteForce:
            taskMgr.setupTaskChain('blockSizeUpdateChain', numThreads=1, tickClock=0,
                                   threadPriority=0, frameBudget=0.1,
                                   frameSync=False, timeslicePriority=True)
            taskMgr.add(self.blockSizeUpdateTask, "blockSizeUpdate",
                        taskChain='blockSizeUpdateChain', sort=99, priority=0)

        #taskMgr.setupTaskChain('terrain', numThreads=3, tickClock=0,
        #                       threadPriority=0, frameBudget=0.1,
        #                       frameSync=False, timeslicePriority=True)
        #taskMgr.add(self.updateTask, 'updateTiles', taskChain='terrain')
        #taskMgr.add(self.tileBuilderTask, 'loadTiles', taskChain='terrain')


    def updateTask(self, task):
        """This task updates each tile, which updates the LOD.

        """

        for pos, tile in self.tiles.items():
            tile.update(task)
            
        return task.again

    def tileBuilderTask(self, task):
        """This task adds and removes tiles as needed."""

        self.makeNewTile(self.focus.getX(), self.focus.getY())
        self.removeOldTiles(self.focus.getX(), self.focus.getY())

        return task.again

    def blockSizeUpdateTask(self, task):

        x = self.focus.getX()
        y = self.focus.getY()
        center = self.tileSize * 0.5

        for pos, tile in self.tiles.items():
            deltaX = x - tile.xOffset + center
            deltaY = y - tile.yOffset + center
            distance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
            if distance < self.minTileDistance * 0.20 + center:
                self.setBlockSize(tile, self.blockSize)
            elif distance < self.minTileDistance * 0.50 + center \
                 and distance > self.minTileDistance * 0.25  + center:
                self.setBlockSize(tile, self.midBlockSize)
            elif distance > self.minTileDistance * 0.55  + center:
                self.setBlockSize(tile, self.farBlockSize)

        return task.again

    def setBlockSize(self, tile, size):

        if tile.getBlockSize() == size:
            return

        tile.setBlockSize(size)
        #tile.generate()

    def makeNewTile(self, x, y):
        """generate the closest terrain tile needed."""

        xstart = (int(x) / self.tileSize) * self.tileSize
        ystart = (int(y) / self.tileSize) * self.tileSize
        radius = (self.minTileDistance / self.tileSize + 2) * self.tileSize
        halfTile = self.tileSize * 0.49

        #print xstart, ystart, radius
        vec = 0
        minDistance = 99999.0

        for checkX in range (xstart - radius, xstart + radius, self.tileSize):
            for checkY in range (ystart - radius, ystart + radius, self.tileSize):
                deltaX = x - (checkX + halfTile)
                deltaY = y - (checkY + halfTile)
                distance = math.sqrt(deltaX * deltaX + deltaY * deltaY)

                if distance < self.minTileDistance and distance < minDistance:
                    if not Vec2(checkX, checkY) in self.tiles:
                        minDistance = distance
                        vec = Vec2(checkX, checkY)
        if not vec == 0:
            self.generateTile(vec.getX(), vec.getY())

    def generateTile(self, x, y):
        """Creates a terrain tile at the input coordinates."""

        tile = TerrainTile(self, x, y)
        if (self.lodBlockSize):
            tile.setBlockSize(self.farBlockSize)
        else:
            tile.setBlockSize(self.blockSize)
        tile.make()
        #np = self.attachNewNode("tileNode")
        #np.reparentTo(self)
        #tile.getRoot().reparentTo(np)
        #self.tiles.append(np)
        tile.getRoot().reparentTo(self)
        self.tiles[Vec2(x, y)] = tile

        #texturize tile
        self.texturer.texturize(tile)

        print "tile generated at", x, y
        return tile

    def removeOldTiles(self, x, y):
        """Remove distant tiles to free memory.
        Also reduces the amount of terrain that will need to be occluded.
        Presently distant terrain WILL still be rendered instead of occluded,
        creating additional gpu strain.

        """

        center = self.tileSize * 0.5
        for pos, tile in self.tiles.items():
            deltaX = x - tile.xOffset + center
            deltaY = y - tile.yOffset + center
            distance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
            if distance > self.maxTileDistance:
                self.removeTile(pos, tile)

    def removeTile(self, pos, tile):
        """Removes a specific tile from the Terrain"""

        del self.tiles[pos]
        print "Tile removed from",pos

    def generateNoiseObjects(self):
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
        self.perlin1 = PerlinNoise2(0, 0, 256, seed = self.id)
        self.perlin1.setScale(self.consistency)

        # perlin2 creates the noticeable noise in the terrain
        # without perlin2 everything would look unnaturally smooth and regular
        # increase perlin2 to make the terrain smoother
        self.perlin2 = StackedPerlinNoise2()
        frequencySpread = 3.0
        amplitudeSpread = 3.3
        perlin2a = PerlinNoise2(0, 0, 256,  seed = self.id*2)
        perlin2a.setScale(self.smoothness)
        self.perlin2.addLevel(perlin2a)
        perlin2b = PerlinNoise2(0, 0, 256,  seed = self.id*3+3)
        perlin2b.setScale(self.smoothness / frequencySpread)
        self.perlin2.addLevel(perlin2b, 1 / amplitudeSpread)
        perlin2c = PerlinNoise2(0, 0, 256, seed = self.id*4+4)
        perlin2c.setScale(self.smoothness / (frequencySpread*frequencySpread))
        self.perlin2.addLevel(perlin2c, 1 / (amplitudeSpread*amplitudeSpread))
        perlin2d = PerlinNoise2(0, 0, 256,  seed = self.id*5+5)
        perlin2d.setScale(self.smoothness / (math.pow(frequencySpread,3)))
        self.perlin2.addLevel(perlin2d, 1 / (math.pow(amplitudeSpread,3)))
        perlin2e = PerlinNoise2(0, 0, 256, seed = self.id*6+6)
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

    def setWireFrame(self, state):
    
        self.wireFrame = state
        for pos, tile in self.tiles.items():
            tile.setWireFrame(state)
    
    def toggleWireFrame(self):
    
        self.setWireFrame(not self.wireFrame)

###############################################################################
#   TerrainTexturer
###############################################################################

class TerrainTexturer():
    """Not yet complete or implemented."""

    def __init__(self, terrain):
        """initialize"""
        self.terrain = terrain

    def load(self):
        """Load textures and shaders."""

    def texturize(self, tile):
        """Apply textures and shaders to the inputted tile."""

###############################################################################
#   MonoTexturer
###############################################################################
class MonoTexturer(TerrainTexturer):
    def load(self):
        """single texture"""

        self.ts = TextureStage('ts')
        tex = loader.loadTexture("textures/rock.jpg")
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
    def load(self):
        """texture + detail texture"""

        self.ts1 = TextureStage('ts')
        tex = loader.loadTexture("textures/snow.jpg")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.monoTexture = tex

        self.detailTS = TextureStage('ts2')
        tex = loader.loadTexture("textures/Detail.png")
        tex.setWrapU(Texture.WMMirror)
        tex.setWrapV(Texture.WMMirror)
        self.detailTexture = tex
        self.textureBlendMode = 7
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
        texScale = self.terrain.tileSize/32
        self.texScale = Vec4(texScale, texScale, texScale, 1.0)

        ### Load textures
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

        self.shader = Shader.load('shaders/stephen4.sha', Shader.SLCg)
        #self.shader = Shader.load('shaders/9.sha', Shader.SLCg)
        #self.shader = Shader.load('shaders/filter-vlight.cg', Shader.SLCg)
        #self.terrain.setShaderInput("casterpos", Vec4(100.0,100.0,100.0,100.0))
        #self.terrain.setShaderInput("light", Vec4(100.0,100.0,100.0,100.0))

        ### texture scaling
        texScale = self.terrain.tileSize/32
        self.texScale = Vec4(texScale, texScale, texScale, 1.0)

        ### Load textures
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

        # regionLimits ( max height, min height, slope max, slope min )
        self.region1 = Vec4(transitionHeights.getX() + blendRadius, -999.0, 1, 0)
        self.region2 = Vec4(transitionHeights.getZ() , transitionHeights.getX() - blendRadius, 0.5, 0)
        self.region3 = Vec4(transitionHeights.getZ() + blendRadius, transitionHeights.getX(), 1.0, 0.2)
        self.region4 = Vec4(999.0, transitionHeights.getZ() - blendRadius, 1.0, 0)

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
        root.setTexture(self.ts4, self.tex4)
        root.setTexture(self.detailTS, self.detailTexture)
        root.setTexScale(self.detailTS, 120, 120)

        #root.setShaderInput("region1ColorMap", self.tex1)
        #root.setShaderInput("region2ColorMap", self.tex2)
        #root.setShaderInput("region3ColorMap", self.tex3)
        #root.setShaderInput("region4ColorMap", self.tex4)
        #root.setShaderInput("region1Limits", self.region1)
        #root.setShaderInput("region2Limits", self.region2)
        #root.setShaderInput("region3Limits", self.region3)
        #root.setShaderInput("region4Limits", self.region4)
        #root.setShaderInput('tscale', self.texScale)
        #
        #root.setShader(self.shader)
