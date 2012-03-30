"""
terrain.py: This file contains the terrain engine for panda 3d.

The TerrainTile is a customized version of Panda3d's GeoMipTerrain.

The HeightMap coverts world x,y coordinates into terrain height and is
therefore responsible for the appearance of terrain geometry.

The TerrainTexturer handles all textures and or shaders on the terrain and is
generally responsible for the appearance of the terrain.

The Terrain class ties all of these elements together. It is responsible for
tiling together the terrain tiles and storing their common attributes.
"""
__author__ = "Stephen Lujan"
__date__ = "$Oct 27, 2010 4:47:05 AM$"

import math

from collections import deque
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
from pandac.PandaModules import NodePath
from populator import *
from pstat_debug import pstat
from terraintexturer import *
from terraintile import *
from pandac.PandaModules import PTAFloat
from config import *

"""
    Panda3d GeoMipTerrain tips:
least detail = max detail level = log(block_size) / log(2)
most detail = min detail level = 0
Block size does not effect the detail level. It only limits the max detail level.
Each block in a GeoMipTerrain can set its own detail level on update if
bruteforce is disabled.

    Performance Note:
In creating new tiles GeoMipTerrain.generate() is the biggest performance hit,
taking up about 5/7 of the time spent in Terrain._generateTile().
Most of the remainder is spent in Terrain.getHeight(). Everything else involved
in adding and removing tiles is trivial in practice.
"""


###############################################################################
#   HeightMap
###############################################################################

class HeightMap():
    """HeightMap functionally maps any x and y to the appropriate height for realistic terrain."""

    def __init__(self, id, flatHeight=0.3):

        self.id = id
        # the overall smoothness/roughness of the terrain
        self.smoothness = 150
        # how quickly altitude and roughness shift
        self.consistency = self.smoothness * 12
        # for realism the flatHeight should be at or very close to waterHeight
        self.flatHeight = flatHeight
        #creates noise objects that will be used by the getHeight function
        self.generateNoiseObjects()
        self.normalize()

    def normalize(self):
        #normalize the range of possible heights to be bounded [0,1]
        minmax = []
        for x in range(2):
            for y in range(2):
                minmax.append(self.getPrenormalizedHeight(x, y))
        min = 9999
        max = -9999
        for x in minmax:
            if x < min:
                min = x
            if x > max:
                max = x
        self.normalizerSub = min
        self.normalizerMult = 1.0 / (max-min)

        print "height normalized from [", min, ",", max, "]"

    def generateStackedPerlin(self, perlin, frequency, layers, frequencySpread, amplitudeSpread, id):

        for x in range(layers):
            layer = PerlinNoise2(0, 0, 256, seed=id + x)
            layer.setScale(frequency / (math.pow(frequencySpread, x)))
            perlin.addLevel(layer, 1 / (math.pow(amplitudeSpread, x)))

    def generateNoiseObjects(self):
        """Create perlin noise."""

        # See getHeight() for more details....
        # where perlin 1 is low terrain will be mostly low and flat
        # where it is high terrain will be higher and slopes will be exagerrated
        # increase perlin1 to create larger areas of geographic consistency
        self.perlin1 = StackedPerlinNoise2()
        self.generateStackedPerlin(self.perlin1, self.consistency, 4, 2, 2.5, self.id)

        # perlin2 creates the noticeable noise in the terrain
        # without perlin2 everything would look unnaturally smooth and regular
        # increase perlin2 to make the terrain smoother
        self.perlin2 = StackedPerlinNoise2()
        self.generateStackedPerlin(self.perlin2, self.smoothness, 8, 2, 2.2, self.id + 100)


    def getPrenormalizedHeight(self, p1, p2):
        """Returns the height at the specified terrain coordinates.

        The input is a value from each of the noise functions

        """

        fh = self.flatHeight
        # p1 varies what kind of terrain is in the area, p1 alone would be smooth
        # p2 introduces the visible noise and roughness
        # when p1 is high the altitude will be high overall
        # when p1 is close to fh most of the visible noise will be muted
        return (p1 - fh + (p1 - fh) * (p2 - fh)) / 2 + fh
        # if p1 = fh, the whole equation simplifies to...
        # 1. (fh - fh + (fh - fh) * (p2 - fh)) / 2 + fh
        # 2. ( 0 + 0 * (p2 - fh)) / 2 + fh
        # 3. (0 + 0 ) / 2 + fh
        # 4. fh
        # The important part to understanding the equation is at step 2.
        # The closer p1 is to fh, the smaller the mutiplier for p2 becomes.
        # As p2 diminishes, so does the roughness.

    #@pstat
    def getHeight(self, x, y):
        """Returns the height at the specified terrain coordinates.

        The values returned should be between 0 and 1 and use the full range.
        Heights should be the smoothest and flatest at flatHeight.

        """
        p1 = (self.perlin1(x, y) + 1) / 2 # low frequency
        p2 = (self.perlin2(x, y) + 1) / 2 # high frequency

        return (self.getPrenormalizedHeight(p1, p2)-self.normalizerSub) * self.normalizerMult

###############################################################################
#   Terrain
###############################################################################

class Terrain(NodePath):
    """A terrain contains a set of geomipmaps, and maintains their common properties."""

    def __init__(self, name, focus, maxRange, populator=None, feedBackString=None, id=0):
        """Create a new terrain centered on the focus.

        The focus is the NodePath where the LOD is the greatest.
        id is a seed for the map and unique name for any cached heightmap images

        """

        NodePath.__init__(self, name)

        ### Basic Parameters
        self.name = name
        # nodepath to center of the level of detail
        self.focus = focus
        # stores all terrain tiles that make up the terrain
        self.tiles = {}
        # stores previously built tiles we can readd to the terrain
        self.storage = {}
        self.feedBackString = feedBackString
        if populator == None:
            populator = TerrainPopulator()
        self.populator = populator

        ##### Terrain Tile physical properties
        self.maxHeight = 300.0
        self.tileSize = 64
        self.heightMapSize = self.tileSize + 1

        ##### Terrain scale and tile distances
        # distances are measured in tile's smallest unit
        # conversion to world units may be necessary
        # Don't show untiled terrain below this distance etc.
        # scale the terrain vertically to its maximum height
        self.setSz(self.maxHeight)
        # scale horizontally to appearance/performance balance
        self.horizontalScale = 1.0
        self.setSx(self.horizontalScale)
        self.setSy(self.horizontalScale)
        # waterHeight is expressed as a multiplier to the max height
        self.waterHeight = 0.3

        #this is the furthest the camera can view
        self.maxViewRange = maxRange
        # Add half the tile size because distance is checked from the center,
        # not from the closest edge.
        self.minTileDistance = self.maxViewRange + self.tileSize * self.horizontalScale / 2
        # make larger to avoid excess loading when milling about a small area
        # make smaller to reduce geometry and other overhead
        self.maxTileDistance = self.minTileDistance + self.tileSize * 0.5

        ##### heightmap properties
        self.initializeHeightMap(id)

        ##### rendering properties
        self.initializeRenderingProperties()

        ##### task handling
        self._setupSimpleTasks()
        #self._setupThreadedTasks()

        # newTile is a placeholder for a tile currently under construction
        # this has to be initialized last because it requires values from self
        #self.newTile = TerrainTile(self, 0, 0)
        # loads all terrain tiles in range immediately
        #self.preload(self.focus.getX() / self.horizontalScale, self.focus.getY() / self.horizontalScale)

    def initializeHeightMap(self, id=0):
        """ """

        print "initializing heightmap..."

        if id == 0:
            self.dice = RandomNumGen(TimeVal().getUsec())
            id = self.dice.randint(2, 1000000)
        self.id = id

        #Remove old tiles that will not conform to a new heightmap
        for pos, tile in self.tiles.items():
            self.removeTile(pos)

        self.heightMap = HeightMap(id, self.waterHeight + 0.03)
        self.getHeight = self.heightMap.getHeight

    def initializeRenderingProperties(self):
        print "initializing terrain rendering properties..."
        self.bruteForce = True
        #self.bruteForce = False
        if self.bruteForce:
            self.blockSize = self.tileSize
        else:
            self.blockSize = 16
            self.near = 40
            self.far = 100
        self.wireFrame = 0
        #self.texturer = MonoTexturer(self)
        self.texturer = ShaderTexturer(self)
        #self.texturer = DetailTexturer(self)
        #self.texturer.apply(self)
        #self.setShaderInput("zMultiplier", )
        print "rendering properties initialized..."

    def _setupSimpleTasks(self):
        """This sets up tasks to maintain the terrain as the focus moves."""

        print "initializing terrain update task..."

        ##Add tasks to keep updating the terrain
        #taskMgr.add(self.updateTilesTask, "updateTiles", sort=9, priority=0)
        self.buildQueue = deque()
        taskMgr.add(self.update, "update", sort=9, priority=0)
        
    def update(self, task):
        """This task updates terrain as needed."""

        self.makeNewTile()
        self.removeOldTiles()
        #self.tileLodUpdate()
        #self.buildDetailLevels()
        
        return task.again

    def updateLight(self):
        """This task moves point and directional lights.

        For larger projects this should be externalized.

        """

        self.pointLight = vec3(0, 5, 0)#self.focus.getPos() + vec3(0,5,0)
        self.setShaderInput("LightPosition", self.pointLight)

    def updateTiles(self):
        """This task updates each tile, which updates the LOD.

        GeoMipMap updates are slow however and may cause unacceptable lag.
        """

        for pos, tile in self.tiles.items():
            tile.update(task)
    
    def tileLodUpdate(self):
        """Unused! LOD causes exposed terrain seams.
        
        Updates tiles to LOD appropriate for their distance.
        
        setMinDetailLevel() doesn't flag a geomipterrain as dirty, so update
        will not alter detail level. It would have to be regenerated.
        Instead we will use a special LodTerrainTile.
        """
        
        x = self.focus.getX() / self.horizontalScale
        y = self.focus.getY() / self.horizontalScale
        center = self.tileSize * 0.5

        # switch to high, mid, and low LOD's at these distances
        # having a gap between the zones avoids switching back and forth too
        # if the focus is moving erratically
        highOuter = self.minTileDistance * 0.20 + center
        highOuter *= highOuter
        midInner = self.minTileDistance * 0.25 + center
        midInner *= midInner
        midOuter = self.minTileDistance * 0.50 + center
        midOuter *= midOuter
        lowInner = self.minTileDistance * 0.55 + center
        lowInner *= lowInner
        
        for pos, tile in self.tiles.items():
            deltaX = x - pos[0] + center
            deltaY = y - pos[1] + center
            distance = deltaX * deltaX + deltaY * deltaY
            if distance < highOuter:
                tile.setDetail(0)
            elif distance < midOuter and distance > midInner:
                tile.setDetail(1)
            elif distance > lowInner:
                tile.setDetail(2)
             
    def buildDetailLevels(self):
        """Unused."""
        
        n = len(self.buildQueue) / 5.0
        if n > 0 and n < 1:
            n = 1
        else:
            n = int(n)
        
        for i in range(n):
            request = self.buildQueue.popleft()
            request[0].buildAndSet(request[1])
            
    def preload(self, xpos=1, ypos=1):
        """Loads all tiles in range immediately.

        This can suspend the program for a long time and is best used when
        first loading a level. It simply iterates through a square region
        building any tile that is reasonably within the max distance. It does not
        prioritize tiles closest to the focus.

        """

        print "preloading terrain tiles..."

        # x and y start are rounded to the nearest multiple of tile size
        xstart = (int(xpos / self.horizontalScale) / self.tileSize) * self.tileSize
        ystart = (int(ypos / self.horizontalScale) / self.tileSize) * self.tileSize
        # check radius is rounded up to the nearest tile size from maxTileDistance
        # not every tile in checkRadius will be made
        checkRadius = (int(self.maxTileDistance) / self.tileSize + 1) * self.tileSize
        halfTile = self.tileSize * 0.5
        # build distance for the preloader will be halfway in between the normal
        # load distance and the unloading distance
        buildDistanceSquared = (self.minTileDistance + self.maxTileDistance) / 2
        buildDistanceSquared = buildDistanceSquared * buildDistanceSquared

        for x in range (xstart - checkRadius, xstart + checkRadius, self.tileSize):
            for y in range (ystart - checkRadius, ystart + checkRadius, self.tileSize):
                if not (x, y) in self.tiles:
                    deltaX = xpos - (x + halfTile)
                    deltaY = ypos - (y + halfTile)
                    distanceSquared = deltaX * deltaX + deltaY * deltaY

                    if distanceSquared < buildDistanceSquared:
                        self.buildQueue.append((x, y))

        total = len(self.buildQueue)
        while len(self.buildQueue):
            if self.feedBackString:
                self.feedBackString = "Loading Terrain " + str(total-len(self.buildQueue)) + "/" + str(total)
                #showFrame()
            tile = self.buildQueue.popleft()
            self._generateTile(tile)

    #@pstat
    def makeNewTile(self):
        """Generate the closest terrain tile needed."""

        # tiles are placed under the terrain node path which may be scaled
        x = self.focus.getX() / self.horizontalScale
        y = self.focus.getY() / self.horizontalScale
        # start position is the focus position rounded to the multiple of tile size
        xstart = (int(x) / self.tileSize) * self.tileSize
        ystart = (int(y) / self.tileSize) * self.tileSize
        # radius is rounded up from minTileDistance to nearest multiple of tile size
        # not every tile within checkRadius will be made
        checkRadius = (self.minTileDistance / self.tileSize + 1) * self.tileSize
        halfTile = self.tileSize * 0.49
        tiles = self.tiles

        #print xstart, ystart, checkRadius
        vec = 0
        minFoundDistance = 9999999999.0
        minDistanceSq = self.minTileDistance * self.minTileDistance

        for checkX in range (xstart - checkRadius, xstart + checkRadius, self.tileSize):
            for checkY in range (ystart - checkRadius, ystart + checkRadius, self.tileSize):
                if not (checkX, checkY) in tiles:
                    deltaX = x - (checkX + halfTile)
                    deltaY = y - (checkY + halfTile)
                    distanceSq = deltaX * deltaX + deltaY * deltaY

                    if distanceSq < minDistanceSq and distanceSq < minFoundDistance:
                        minFoundDistance = distanceSq
                        vec = (checkX, checkY)
        if not vec == 0:
            #print distance," < ",self.minTileDistance," and ",distance," < ",minDistance
            #self.generateTile(vec.getX(), vec.getY())
            self._generateTile(vec)

    def dispatchNewTileAt(self, x, y):
        """Dispatch a task to create a tile at the input coordinates."""

        #self.newTile.xOffset = x
        #self.newTile.yOffset = y
        #self.tiles[(x, y)] = self.newTile
        #_generateTile((x,y))
        taskMgr.add(self._generateTileTask, name="_generateTile",
                    extraArgs=[(x, y)], appendTask=True,
                    taskChain='tileGenerationQueue', sort=1, priority=1)

    #@pstat
    def _generateTile(self, pos):
        """Creates a terrain tile at the input coordinates."""

        if pos in self.storage:
            tile = self.storage[pos]
            self.tiles[pos] = tile
            tile.getRoot().reparentTo(self)
            del self.storage[pos]
            print "tile recovered from storage at", pos
            return
        
        if SAVED_TEXTURE_MAPS:
            tile = TextureMappedTerrainTile(self, pos[0], pos[1])
        else:
            tile = TerrainTile(self, pos[0], pos[1])
        tile.make()
        tile.getRoot().reparentTo(self)
        self.tiles[pos] = tile

        #texturize tile
        #self.texturer.texturize(tile)

        self.populator.populate(tile)

        print "tile generated at", pos
        return tile

    #@pstat
    def removeOldTiles(self):
        """Remove distant tiles to free system resources."""

        x = self.focus.getX() / self.horizontalScale
        y = self.focus.getY() / self.horizontalScale
        center = self.tileSize * 0.5
        maxDistanceSquared = self.maxTileDistance * self.maxTileDistance
        for pos, tile in self.tiles.items():
            deltaX = x - (pos[0] + center)
            deltaY = y - (pos[1] + center)
            distance = deltaX * deltaX + deltaY * deltaY
            if distance > maxDistanceSquared:
                #print distance, " > ", self.maxTileDistance * self.maxTileDistance
                self.storeTile(pos)

    def storeTile(self, pos):
        tile = self.tiles[pos]
        tile.getRoot().detachNode()
        self.storage[pos]= tile
        del self.tiles[pos]
        print "Tile removed from", pos

    def deleteTile(self, pos):
        """Removes a specific tile from the Terrain."""

        self.tiles[pos].getRoot().detachNode()
        del self.tiles[pos]
        print "Tile deleted from", pos

    def getElevation(self, x, y):
        """Returns the height of the terrain at the input world coordinates."""

        return self.getHeight(x / self.horizontalScale, y / self.horizontalScale) * self.getSz()

    def setWireFrame(self, state):
        self.wireFrame = state
        if state:
            self.setRenderModeWireframe()
        else:
            self.setRenderModeFilled()
        #for pos, tile in self.tiles.items():
        #    tile.setWireFrame(state)

    def toggleWireFrame(self):
        self.setWireFrame(not self.wireFrame)

    def test(self):
        self.texturer.test()
        
    def setShaderFloatInput(self, name, input):
        print "set shader input ",name," to ",input
        self.setShaderInput(name, PTAFloat([input]))
