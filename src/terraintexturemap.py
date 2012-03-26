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
        self.image = PNMImage()
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

    def calculateWeight(self, value, minimum, maximum):

        if value > maximum:
            #print "value > maximum"
            return 0
        if value < minimum:
            #print "value < minimum"
            return 0

        weight = min(maximum - value, value - minimum)
        #print "min(",maximum," - ", value," , ", value ," - ",minimum,") =",weight

        return weight


    def calculateFinalWeight(self, height, slope, limits):
        #print "calculateFinalWeight(",height, slope, limits,")"

        height = self.calculateWeight(height, limits.x, limits.y)
        slope = self.calculateWeight(slope, limits.z, limits.w)
        #print "height * slope =", height * slope
        return height * slope


    def calculateTextures(self, terrainTile):

        size = self.terrain.tileSize + 1
        #getNormal = self.getNormal
        getSlope = terrainTile.slopeMap.getGray
        #slopeMult = self.terrain.maxHeight / self.terrain.horizontalScale
        getHeight = terrainTile.image.getGray
        maxHeight = self.terrain.maxHeight
        calculateFinalWeight = self.calculateFinalWeight
        textures = self.textures

        for tex in textures:
            tex.image = PNMImage(size, size, 3)

        for x in range(size):
            for y in range(size):
                slope = getSlope(x, y)
                height = getHeight(x, y) * maxHeight
                textureWeightTotal = 0.000001;

                for tex in textures:
                    tex.weight = 0.0;
                    for region in tex.regions:
                        weight = calculateFinalWeight(height, slope, region)
                        tex.weight += weight
                        textureWeightTotal += weight
                        #print tex.weight
                for tex in textures:
                    #print "setGray(", x, y, "  tex.weight / textureWeightTotal =",tex.weight / textureWeightTotal
                    tex.image.setGray(x, y, tex.weight / textureWeightTotal)
                    #print tex.image.getGray(x,y)
                    #tex.image.setAlpha(x, y, 0.3)
                    #tex.image.setAlpha(5, 5, 0.25)
