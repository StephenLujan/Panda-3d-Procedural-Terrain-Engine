###
# This file contains the terrain tile used by Terrain.
#
# The TerrainTile is a customized instance of Panda3d's GeoMipTerrain.
# The Terrain class holds all of the common properties TerrainTiles
# can use, such as the height function, tile size, and the TerrainTexturer.
#
###
__author__ = "Stephen"
__date__ = "$Oct 27, 2010 4:47:05 AM$"

from pandac.PandaModules import Filename
from pandac.PandaModules import GeoMipTerrain
from pandac.PandaModules import NodePath
from pandac.PandaModules import PNMImage
#from pandac.PandaModules import Vec2
from pstat_debug import pstat

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
        self.detail = 1 # higher means greater detail

        #name = "ID" + str(terrain.id) + "X" + str(x) + "Y" + str(y)
        GeoMipTerrain.__init__(self, name=terrain.name)

        #self.mapName = "heightmaps/" + name + ".png"
        self.image = PNMImage()

        self.getRoot().setPos(x, y, 0)
        GeoMipTerrain.setFocalPoint(self, terrain.focus)
        if self.terrain.bruteForce:
            GeoMipTerrain.setBruteforce(self, True)
            GeoMipTerrain.setBlockSize(self, self.terrain.heightMapSize * self.detail)
        else:
            GeoMipTerrain.setBlockSize(self, 16)
            self.setBorderStitching(1)
            self.setNear(self.terrain.near)
            self.setFar(self.terrain.far)
        self.setAutoFlatten(GeoMipTerrain.AFMStrong)

    def update(self, dummy):
        """Updates the GeoMip to use the correct LOD on each block."""

        GeoMipTerrain.update(self)

    def updateTask(self, task):
        """Updates the GeoMip to use the correct LOD on each block."""

        self.update(task)
        return task.again
    #@pstat
    def setHeightField(self, filename):
        """Set the GeoMip heightfield from a heightmap image."""

        GeoMipTerrain.setHeightfield(self, filename)

    @pstat
    def setHeight(self):
        """Sets the height field to match the height map image."""

        self.setHeightField(self.image)

    @pstat
    def makeHeightMap(self):
        """Generate a new heightmap image.

        Panda3d GeoMipMaps require an image from which to build and update
        their height field. This function creates the correct image using the
        tile's position and the Terrain's getHeight() function.

        """

        heightMapSize = self.terrain.tileSize * self.detail + 1
        self.image = PNMImage(heightMapSize, heightMapSize)
        self.image.makeGrayscale()
        self.image.setMaxval(65535)


        ySize = self.image.getYSize() - 1
        getHeight = self.terrain.getHeight
        setGray = self.image.setGray
        xo = self.xOffset
        yo = self.yOffset
        d = self.detail

        for x in range(self.image.getXSize()):
            for y in range(ySize + 1):
                height = getHeight(x / d + xo, y / d + yo)
                #  feed pixel into image
                # why is it necessary to invert the y axis I wonder?
                setGray(x, ySize - y, height)
        #self.postProcessImage()
        #self.image.write(Filename(self.mapName))

    def postProcessImage(self):
        """Perform filters and manipulations on the heightmap image."""

        #self.image.gaussianFilter()

    def wireframe(self):
        self.getRoot().setRenderModeWireframe()

    def makeSlopeMap(self):
        print "makeSlopeMap"
        self.slopeMap = PNMImage(self.terrain.heightMapSize, self.terrain.heightMapSize)
        self.slopeMap.makeGrayscale()
        self.slopeMap.setMaxval(65535)

        size = self.slopeMap.getYSize()
        getNormal = self.getNormal
        setGray = self.slopeMap.setGray

        for x in range(size):
            for y in range(size):
                slope = getNormal(x, y).z
                #  feed pixel into image
                # why is it necessary to invert the y axis I wonder?
                setGray(x, y, normal)
        #self.getNormal (int x, int y)
 	#Fetches the terrain normal at (x, y), where the input coordinate is specified in pixels.
    @pstat
    def make(self):
        """Build a finished renderable heightMap."""

        self.getRoot().setSx(1.0 / self.detail)
        self.getRoot().setSy(1.0 / self.detail)
        self.makeHeightMap()
        self.setHeight()
        #self.getRoot().setSz(self.maxHeight)
        self.generate()
        self.terrain.texturer.apply(self.getRoot())



###############################################################################
#   CachingTerrainTile !! UNUSED !!
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
#   LodTerrainTile !! UNUSED !!
###############################################################################

class LodTerrainTile(TerrainTile):
    """Always builds full detail heightmap, but uses panda3d's default LOD
    functions, and hides seams between tiles."""

    def __init__(self, terrain, x, y):
        """Builds a Tile for the terrain at input coordinates."""

        TerrainTile.__init__(self, terrain, x, y)
        self.detail = 2
        self.setMinLevel(2)
        self.make()

    def setDetail(self, detail):
        if self.detail == detail:
            return
        self.detail = detail
        self.setMinLevel(detail)
        self.generate()
        self.getRoot().setPos(self.xOffset, self.yOffset, 0)


###############################################################################
#   LodTerrainTile2 !! UNUSED !!
###############################################################################

class LodTerrainTile2(NodePath):
    """Very fast but leaves obvious seams."""

    def __init__(self, terrain, x, y):
        """Builds a Tile for the terrain at input coordinates."""

        NodePath.__init__(self, terrain.name)
        self.setMinDetail(2)
        self.make()

    def setDetail(self, detail):
        if self.detail == detail:
            return
        self.detail = detail
        if detail in self.detailLevels:
            self._setDetail(detail)
        else:
            self.terrain.buildQueue.append((self, detail))

    def _setDetail(self, detail):
        for d, tile in self.detailLevels.iteritems():
            if not d == detail:
                #PandaNode.stashChild(self, tile)
                tile.getRoot().stash()
            else:
                #PandaNode.unstashChild(self, tile)
                tile.getRoot().unstash()

    def buildAndSet(self, detail):
        self.detailLevels[detail] = self.build(detail)
        self._setDetail(detail)
