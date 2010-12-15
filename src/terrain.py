###
# This file contains the terrain engine for panda 3d.

__author__ = "Stephen"
__date__ = "$Oct 27, 2010 4:47:05 AM$"

import math
from operator import itemgetter

from direct.showbase.RandomNumGen import *
from direct.task.Task import Task
from panda3d.core import BitMask32
from panda3d.core import CollisionHandlerQueue
from panda3d.core import CollisionNode
from panda3d.core import CollisionRay
from panda3d.core import CollisionTraverser
from panda3d.core import PNMImage
from panda3d.core import PerlinNoise2
from panda3d.core import StackedPerlinNoise2
from panda3d.core import TimeVal
from pandac.PandaModules import Filename
from pandac.PandaModules import GeoMipTerrain
from pandac.PandaModules import NodePath
from pandac.PandaModules import PandaNode
from pandac.PandaModules import Point3
from pandac.PandaModules import Vec2

from terraintexturer import *

""" Panda3d GeoMipTerrain tips:
least detail = max detail level = log(block_size) / log(2)
most detail = min detail level = 0
Block size does not effect the detail level. It only limits the max detail level.
Each block in a GeoMipTerrain can set its own detail level on update if
bruteforce is disabled.
"""

###############################################################################
#   TerrainTile
###############################################################################

class TerrainTile(GeoMipTerrain):
    """TerrainTiles are the building blocks of a terrain."""

    def __init__(self, terrain, x, y):
        """Builds a Tile for the terrain at input coordinates.

        Important settings are used directly from the terrain.
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
            GeoMipTerrain.setBruteforce(self, True)
        else:
            self.setBorderStitching(1)
            self.setNear(self.terrain.near)
            self.setFar(self.terrain.far)

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
        """Sets the height field to match the height map image."""

        self.setHeightField(self.image)

    def makeHeightMap(self):
        """Generate a new heightmap image.

        Panda3d GeoMipMaps require an image from which to build and update
        their height field. This function creates the correct image using the
        tile's position and the Terrain's getHeight() function

        """

        self.image = PNMImage(self.terrain.heightMapSize, self.terrain.heightMapSize)
        self.image.makeGrayscale()
        # these may be redundant
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

        ySize = self.image.getYSize()
        getHeight = self.terrain.getHeight
        setGray = self.image.setGray

        for x in range(self.image.getXSize()):
            for y in range(ySize):
                height = getHeight(x + self.xOffset, y + self.yOffset)
                #  feed pixel into image
                # why is it necessary to invert the y axis I wonder?
                setGray(x, ySize-1-y, height)
        #self.postProcessImage()
        #self.image.write(Filename(self.mapName))

    def postProcessImage(self):
        """Perform filters and manipulations on the heightmap image."""

        #self.image.gaussianFilter()

    def wireframe(self):
        self.getRoot().setRenderModeWireframe()

    def make(self):
        """Build a finished renderable heightMap."""

        self.makeHeightMap()
        self.setHeight()
        #self.getRoot().setSz(self.maxHeight)
        self.generate()


###############################################################################
#   CachingTerrainTile
###############################################################################

class CachingTerrainTile(TerrainTile):
    """Unused!

    This TerrainTile will use cached heightmap images if possible.
    If it is not possible it will create new images and save them to disk.

    """
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
        TerrainTile.makeHeightMap(self)
        self.image.write(Filename(self.mapName))


###############################################################################
#   Terrain
###############################################################################

class Terrain(NodePath):
    """A terrain contains a set of geomipmaps, and maintains their common properties."""

    def __init__(self, name, focus, id=0):
        """Create a new terrain centered on the focus.

        The focus is the NodePath where the LOD is the greatest.
        id is a seed for the map and unique name for any cached heightmap images

        """

        NodePath.__init__(self, name)

        self.name = name

        ##### tile physical properties
        self.maxHeight = 350
        self.tileSize = 64
        self.heightMapSize = self.tileSize + 1

        ##### heightmap properties
        # the overall smoothness/roughness of the terrain
        self.smoothness = 55
        # how quickly altitude and roughness shift
        self.consistency = self.smoothness * 8
        self.waterHeight = 0.3 # out of a max of 1.0
        # for realism the flatHeight should be at or very close to waterHeight
        self.flatHeight = self.waterHeight + 0.07
        self.dice = RandomNumGen(TimeVal().getUsec())
        if id == 0:
            id = self.dice.randint(2, 1000000)
        self.id = id
        #creates noise objects that will be used by the getHeight function
        self.generateNoiseObjects()

        ##### Terrain scale and tile distances
        # Don't show untiled terrain below this distance etc.
        self.maxViewRange = 500
        # Add half the tile size because distance is checked from the center,
        # not from the closest edge.
        self.minTileDistance = self.maxViewRange + self.tileSize / 2
        # make larger to avoid excess loading when milling about a small area
        # make smaller to shrink some overhead
        self.maxTileDistance = self.minTileDistance * 1.3 + self.tileSize
        self.focus = focus
        #scale the terrain vertically to its maximum height
        self.setSz(self.maxHeight)
        self.horizontalScale = 1.5
        self.setSx(self.horizontalScale)
        self.setSy(self.horizontalScale)

        ##### rendering properties
        self.bruteForce = True
        if self.bruteForce:
            self.blockSize = self.tileSize
        else:
            self.blockSize = 16
            self.near = 40
            self.far = 100
        self.wireFrame = 0
        self.texturer = ShaderTexturer(self)
        #self.texturer = DetailTexturer(self)
        self.texturer.load()


        #####
        # stores all terrain tiles that make up the terrain
        self.tiles = {}
        #currently unused
        self.setupElevationRay()
        #this is a placeholder for a tile currently under construction
        self.dummyTile = TerrainTile(self, 0, 0)
        #self._setupSimpleTasks()
        self._setupThreadedTasks()
        #loads all terrain tiles in range immediately
        self.preload(self.focus.getX() / self.horizontalScale, self.focus.getY() / self.horizontalScale)

    def _setupSimpleTasks(self):
        """This sets up tasks to maintain the terrain as the focus moves."""

        ##Add tasks to keep updating the terrain
        #taskMgr.add(self.updateTask, "updateTiles", sort=9, priority=0)
        taskMgr.add(self.tileBuilderTask, "loadTiles", sort=9, priority=0)

    def _setupThreadedTasks(self):
        """This sets up tasks to maintain the terrain as the focus moves."""

        ##Add tasks to keep updating the terrain
        ##def setupTaskChain(self, chainName, numThreads=None, tickClock=None,
        ##        threadPriority=None, frameBudget=None, timeslicePriority=None)

        #taskMgr.setupTaskChain('updateTilesChain', numThreads=1, tickClock=0,
        #                       threadPriority=0, frameBudget=0.1,
        #                       frameSync=False, timeslicePriority=True)
        #taskMgr.add(self.updateTask, "updateTiles", taskChain='updateTilesChain',
        #            sort=1, priority=0)

        taskMgr.setupTaskChain('tileBuilderChain', numThreads=1, tickClock=0,
                               threadPriority=1, frameBudget=0.2,
                               frameSync=False, timeslicePriority=True)
        taskMgr.add(self.tileBuilderTask, "loadTiles", taskChain='tileBuilderChain',
                    sort=1, priority=0)

        taskMgr.setupTaskChain('tileGenerationQueue', numThreads=3, tickClock=0,
                               threadPriority=1, frameBudget=0.2,
                               frameSync=False, timeslicePriority=True)

        #if self.bruteForce:
        #    taskMgr.setupTaskChain('blockSizeUpdateChain', numThreads=1, tickClock=0,
        #                           threadPriority=0, frameBudget=0.1,
        #                           frameSync=False, timeslicePriority=True)
        #    taskMgr.add(self.blockSizeUpdateTask, "blockSizeUpdate",
        #                taskChain='blockSizeUpdateChain', sort=1, priority=0)

    def updateTask(self, task):
        """Deprecated -- This task updates each tile, which updates the LOD."""

        for pos, tile in self.tiles.items():
            tile.update(task)

        return task.again

    def tileBuilderTask(self, task):
        """This task adds and removes tiles as needed."""

        self.makeNewTile(self.focus.getX() / self.horizontalScale, self.focus.getY() / self.horizontalScale)
        self.removeOldTiles(self.focus.getX() / self.horizontalScale, self.focus.getY() / self.horizontalScale)

        return task.again

    def tileLodUpdateTask(self, task):
        """Deprecated."""

        x = self.focus.getX() / self.horizontalScale
        y = self.focus.getY() / self.horizontalScale
        center = self.tileSize * 0.5

        # switch to high, mid, and low LOD's at these distances
        # having a gap between the zones avoids switching back and forth too
        # if the focus is moving erratically
        hlEnd   = self.minTileDistance * 0.20 + center
        mlStart = self.minTileDistance * 0.25 + center
        mlEnd   = self.minTileDistance * 0.50 + center
        llStart = self.minTileDistance * 0.55 + center

        for pos, tile in self.tiles.items():
            deltaX = x - tile.xOffset + center
            deltaY = y - tile.yOffset + center
            distance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
            if distance < hlEnd:
                tile.setMinDetailLevel(0)
            elif distance < mlEnd and distance > mlStart:
                tile.setMinDetailLevel(1)
            elif distance > llStart:
                tile.setMinDetailLevel(2)

        return task.again

    def preload(self, xpos=1, ypos=1):
        """Loads all tiles in range immediately.

        This can suspend the program for a long time and is best used when
        first loading a level. It simply iterates through a square region
        building any tile that is reasonably within the max distance. It does not
        prioritize tiles closest to the focus.

        """

        xstart = (int(xpos) / self.tileSize) * self.tileSize
        ystart = (int(ypos) / self.tileSize) * self.tileSize
        radius = (int(self.maxTileDistance) / self.tileSize + 1) * self.tileSize
        halfTile = self.tileSize * 0.5
        maxDistanceSquared = (self.minTileDistance + self.maxTileDistance) / 2
        maxDistanceSquared = maxDistanceSquared * maxDistanceSquared

        for x in range (xstart - radius, xstart + radius, self.tileSize):
            for y in range (ystart - radius, ystart + radius, self.tileSize):
                if not Vec2(x, y) in self.tiles:
                    deltaX = xpos - (x + halfTile)
                    deltaY = ypos - (y + halfTile)
                    distanceSquared = deltaX * deltaX + deltaY * deltaY

                    if distanceSquared < maxDistanceSquared:
                        self._generateTile(x, y)
                        #self.dispatchNewTileAt(x,y)

    def makeNewTile(self, x, y):
        """Generate the closest terrain tile needed."""

        xstart = (int(x) / self.tileSize) * self.tileSize
        ystart = (int(y) / self.tileSize) * self.tileSize
        radius = (self.minTileDistance / self.tileSize + 1) * self.tileSize
        halfTile = self.tileSize * 0.49

        #print xstart, ystart, radius
        vec = 0
        minFoundDistance = 99999999.0
        minDistanceSq = self.minTileDistance * self.minTileDistance

        for checkX in range (xstart - radius, xstart + radius, self.tileSize):
            for checkY in range (ystart - radius, ystart + radius, self.tileSize):
                if not Vec2(checkX, checkY) in self.tiles:
                    deltaX = x - (checkX + halfTile)
                    deltaY = y - (checkY + halfTile)
                    distanceSq = deltaX * deltaX + deltaY * deltaY

                    if distanceSq < minDistanceSq and distanceSq < minFoundDistance:
                        minFoundDistance = distanceSq
                        vec = Vec2(checkX, checkY)
        if not vec == 0:
            #print distance," < ",self.minTileDistance," and ",distance," < ",minDistance
            #self.generateTile(vec.getX(), vec.getY())
            self.dispatchNewTileAt(vec.getX(), vec.getY())

    def dispatchNewTileAt(self, x, y):
        """Dispatch a task to create a tile at the input coordinates."""
        self.dummyTile.xOffset = x
        self.dummyTile.yOffset = y
        self.tiles[Vec2(x, y)] = self.dummyTile
        taskMgr.add(self._generateTileTask, name="_generateTile",
                    extraArgs=[x, y], appendTask=True,
                    taskChain='tileGenerationQueue', sort=1, priority=1)

    def _generateTileTask(self, x, y, task):
        """Task wrapper for _generateTile. Probably redundant now..."""
        self._generateTile(x, y)
        return task.done

    def _generateTile(self, x, y):
        """Creates a terrain tile at the input coordinates."""

        tile = TerrainTile(self, x, y)
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
        """Remove distant tiles to free system resources."""

        center = self.tileSize * 0.5
        for pos, tile in self.tiles.items():
            deltaX = x - (tile.xOffset + center)
            deltaY = y - (tile.yOffset + center)
            distance = deltaX * deltaX + deltaY * deltaY
            if distance > self.maxTileDistance * self.maxTileDistance:
                #print distance, " > ", self.maxTileDistance * self.maxTileDistance
                self.removeTile(pos, tile)

    def removeTile(self, pos, tile):
        """Removes a specific tile from the Terrain."""

        self.tiles[pos].getRoot().detachNode()
        del self.tiles[pos]
        print "Tile removed from", pos

    def generateNoiseObjects(self):
        """Create perlin noise."""

        # See getHeight() for more details....

        # where perlin 1 is low terrain will be mostly low and flat
        # where it is high terrain will be higher and slopes will be exagerrated
        # increase perlin1 to create larger areas of geographic consistency
        self.perlin1 = StackedPerlinNoise2()
        perlin1a = PerlinNoise2(0, 0, 256, seed=self.id)
        perlin1a.setScale(self.consistency)
        self.perlin1.addLevel(perlin1a)
        perlin1b = PerlinNoise2(0, 0, 256, seed=self.id*2+123)
        perlin1b.setScale(self.consistency/2)
        self.perlin1.addLevel(perlin1b,1/2)


        # perlin2 creates the noticeable noise in the terrain
        # without perlin2 everything would look unnaturally smooth and regular
        # increase perlin2 to make the terrain smoother
        self.perlin2 = StackedPerlinNoise2()
        frequencySpread = 3.0
        amplitudeSpread = 3.4
        perlin2a = PerlinNoise2(0, 0, 256, seed=self.id * 2)
        perlin2a.setScale(self.smoothness)
        self.perlin2.addLevel(perlin2a)
        perlin2b = PerlinNoise2(0, 0, 256, seed=self.id * 3 + 3)
        perlin2b.setScale(self.smoothness / frequencySpread)
        self.perlin2.addLevel(perlin2b, 1 / amplitudeSpread)
        perlin2c = PerlinNoise2(0, 0, 256, seed=self.id * 4 + 4)
        perlin2c.setScale(self.smoothness / (frequencySpread * frequencySpread))
        self.perlin2.addLevel(perlin2c, 1 / (amplitudeSpread * amplitudeSpread))
        perlin2d = PerlinNoise2(0, 0, 256, seed=self.id * 5 + 5)
        perlin2d.setScale(self.smoothness / (math.pow(frequencySpread, 3)))
        self.perlin2.addLevel(perlin2d, 1 / (math.pow(amplitudeSpread, 3)))
        perlin2e = PerlinNoise2(0, 0, 256, seed=self.id * 6 + 6)
        perlin2e.setScale(self.smoothness / (math.pow(frequencySpread, 4)))
        self.perlin2.addLevel(perlin2e, 1 / (math.pow(amplitudeSpread, 4)))


    def getHeight(self, x, y):
        """Returns the height at the specified terrain coordinates.

        The values returned should be between 0 and 1 and use the full range.
        Heights should be the smoothest and flatest at flatHeight.

        """

        # all of these should be in the range of 0 to 1
        p1 = (self.perlin1(x, y) + 1) / 2 # low frequency
        p2 = (self.perlin2(x, y) + 1) / 2 # high frequency
        fh = self.flatHeight

        # p1 varies what kind of terrain is in the area, p1 alone would be smooth
        # p2 introduces the visible noise and roughness
        # when p1 is high the altitude will be high overall
        # when p1 is close to fh most of the visible noise will be muted
        return (p1 - fh) / 2 + (p1 - fh) * (p2 - fh) / 4 + fh

    def getElevation(self, x, y):
        """Returns the height of the terrain at the input world coordinates."""

        return self.getHeight(x / self.horizontalScale, y / self.horizontalScale) * self.getSz()

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

