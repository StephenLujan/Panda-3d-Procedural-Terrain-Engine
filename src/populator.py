###
# Author: Stephen Lujan
###
# This file contains code to populate terrain tiles with objects
###
from terraintile import *

class Factory():
    def __init__(self, factoryFunction, constructorParams, averageNumber ):
        self.factoryFunction = factoryFunction
        self.constructorParams = constructorParams
        self.averageNumber = averageNumber

class TerrainPopulator():

    def __init__(self, terrain):
        self.terrain = terrain
        self.factories = []

    def addObject(self, factoryFunction, constructorParams, averageNumber):
        factory = Factory(factoryFunction, constructorParams, averageNumber)
        self.factories.append(factory)

    def populate(self, tile):
        xOff = tile.xOffset
        yOff = tile.yOffset
        tileSize = self.terrain.tileSize

        seed = terrain.heightMap.getHeight(yOff * -2, xOff * -2) * 2147483647
        dice = RandomNumGen(seed)
        
        for factory in self.factories:
            num = dice.randint(0, factory.averageNumber) + dice.randint(0, factory.averageNumber)
            for iterator in range(num):
                x = dice.random() * tileSize
                y = dice.random() * tileSize
                object = factory.factoryFunction(*factory.constructorParams)
                self.add(tile, object, x, y)

    def add(self, tile, object, x, y):

        object.reparentTo(tile)
        z = self.terrain.getHeight(x + tile.xOffset, y + tile.yOffset)
        object.setPos(x, y, z)
