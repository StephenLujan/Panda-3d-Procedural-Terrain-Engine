###
# Author: Stephen Lujan
###
# This file contains the TextureMapper class and its constituents
###

class TerrainShaderTexture:

    def __init__(self, tex):

        self.tex = tex
        self.regions = []

    def addRegion(self, region):

        self.regions.append(region)


class TextureMapper:
    """Collects all textures used by the terrain and stores regional boundries for each."""

    def __init__(self):
        self.textures = []

    def addTexture(self, texture):

        self.textures.append(TerrainShaderTexture(texture))

    def addRegionToTex(self, region, textureNumber=-1):

        #bail out if there are no textures to avoid crash
        if len(self.textures) < 1:
            return
        #default to the last texture
        if textureNumber == -1:
            textureNumber = len(self.textures) - 1

        self.textures[textureNumber].addRegion(region)