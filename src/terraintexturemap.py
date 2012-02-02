###
# Author: Stephen Lujan
###
# This file contains the TextureMapper class and its constituents
###

from pandac.PandaModules import PNMImage
from pandac.PandaModules import Vec4

class TerrainShaderTexture:

    def __init__(self, tex, terrain):

        self.tex = tex
        self.regions = []
        self.terrain = terrain
        size = self.terrain.tileSize + 1
        self.image = PNMImage(size, size, 1, 65535)
        self.weight = 0.0

    def addRegion(self, region):

        self.regions.append(region)


class TextureMapper:
    """Collects all textures used by the terrain and stores regional boundries for each."""

    def __init__(self, terrain):
        self.textures = []
        self.terrain = terrain

    def addTexture(self, texture):

        self.textures.append(TerrainShaderTexture(texture, self.terrain))

    def addRegionToTex(self, region, textureNumber=-1):

        #bail out if there are no textures to avoid crash
        if len(self.textures) < 1:
            return
        #default to the last texture
        if textureNumber == -1:
            textureNumber = len(self.textures) - 1

        self.textures[textureNumber].addRegion(region)

    def calculateWeight(self, value, minimum, maximum ):

        value = clamp(value, minimum, maximum)
        weight = min(maximum - value, value - minimum)

        return weight


    def calculateFinalWeight(self, height, slope, limits ):

        return self.calculateWeight(height, limits.w, limits.x) \
               * self.calculateWeight(slope, limits.y, limits.z)


    def calculateTextures(self, terrainTile):

        size = terrainTile.slopeMap.getYSize()
        #getNormal = self.getNormal
        getSlope = terrainTile.slopeMap.getGray
        getHeight = terrainTile.image.getGray
        calculateFinalWeight = self.calculateFinalWeight
        textures = self.textures

        for x in range(size):
            for y in range(size):
                slope = getSlope(x,y)
                height = getHeight(x,y)
                textureWeightTotal = 0.000001;

                texNum = 0
                regionNum = 0

                for tex in textures:
                    textureWeight = 0.0;
                    for region in tex.regions:

                        textureWeight += calculateFinalWeight(height, slope, region)
