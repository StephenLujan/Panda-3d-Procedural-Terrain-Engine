"""
gui.py: This file contains a gui for the real-time manipulation of settings
related to the terrain engine. This is currently an implementation of Panda3d's
DirectGui.
"""
__author__ = "Stephen Lujan"

from config import *
from direct.gui.DirectGui import *
from direct.gui.DirectGuiBase import DirectGuiWidget
from pandac.PandaModules import TextNode
from pandac.PandaModules import Vec4

###############################################################################
#   SlideControl
###############################################################################
class SlideControl():
    def __init__(self, x, y, parent=aspect2d, range=(0, 100), value=50, xsize=1.0, ysize=1.0, name="Slider Name", function=0):

        self.function = function
        #self.extraArgs = extraArgs
        self.size = (-ysize, ysize, -xsize, xsize)
        self.frame = DirectFrame(parent=parent, frameColor=(0, 0, 0, 0),
                                 frameSize=self.size,
                                 pos=(x, 0, y))

        self.slider = DirectSlider(parent=self.frame, range=range, pos=(0, 0, 0), value=value, pageSize=5, command=self.myFunc)
        self.label = OnscreenText(parent=self.frame, text=name, pos=(-0.7, -0.1), scale=0.15, fg=(1, 0.5, 0.5, 1), align=TextNode.ACenter, mayChange=0)
        self.value = OnscreenText(parent=self.frame, text="slider value", pos=(0.7, -0.1), scale=0.15, fg=(1, 0.5, 0.5, 1), align=TextNode.ACenter, mayChange=1)

        self.resize(self.size)

    def resize(self, size):
        self.size = size
        vertical = size[1]- size[0]
        horizontal = size[3]- size[2]
        self.frame.setScale(horizontal / 2, 1, vertical / 2)
        #self.slider.setScale(horizontal/2, 1, vertical/2)
        #self.slider.setHeight(vertical)

    def myFunc(self):

        if self.function:
            self.function(self.slider.getValue())
            #self.function()
        self.value.setText(str(self.slider.getValue()))

        #children of DirectSliders' can't access value
        #return super(mySlider, self).getValue()
        #return super(mySlider, self)['value']
        #return super(mySlider, self).guiItem.getValue()
        #return DirectSlider.getValue(self)
        #return DirectSlider.guiItem.getValue(self)
        #DirectGuiWidget.guiItem.getValue(self)

###############################################################################
#   ShaderRegionControl
###############################################################################
class ShaderRegionControl():
    def __init__(self, x, y, regionNumber, terrain, parent=aspect2d):

        size = 0.5
        self.size = (-size, size, -size, size)
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0),
                                 frameSize=self.size,
                                 pos=(x, 0, y),
                                 parent=parent
                                 )

        self.regionNumber = regionNumber
        self.terrain = terrain
        self.currentRegion = Vec4(terrain.getShaderInput('region' + str(self.regionNumber) + 'Limits').getVector())
        #logging.info( "shader control panel for region "+ str(regionNumber)+ ": "+ str(self.currentRegion))

        self.minHeight = self.currentRegion[0]
        self.minHeightSlide = SlideControl(0, 0.6, parent=self.frame, range=(-0.1 * terrain.maxHeight, 1.1 * terrain.maxHeight), value=self.minHeight, name="Min Height", function=self.setMinHeight, ysize=1.5, xsize=1.5)
        self.maxHeight = self.currentRegion[1]
        self.maxHeightSlide = SlideControl(0, 0.2, parent=self.frame, range=(-0.1 * terrain.maxHeight, 1.1 * terrain.maxHeight), value=self.maxHeight, name="Max Height", function=self.setMaxHeight, ysize=1.5, xsize=1.5)
        self.minSlope = self.currentRegion[2]
        self.minSlopeSlide = SlideControl(0, -0.2, parent=self.frame, range=(0, 1), value=self.minSlope, name="Min Slope", function=self.setMinSlope, ysize=1.5, xsize=1.5)
        self.maxSlope = self.currentRegion[3]
        self.maxSlopeSlide = SlideControl(0, -0.6, parent=self.frame, range=(0, 1), value=self.maxSlope, name="Max Slope", function=self.setMaxSlope, ysize=1.5, xsize=1.5)

        self.resize(self.size)

    def setMinHeight(self, input):
        self.minHeight = input
        self.setShaderInput()

    def setMaxHeight(self, input):
        self.maxHeight = input
        self.setShaderInput()

    def setMinSlope(self, input):
        self.minSlope = input
        self.setShaderInput()

    def setMaxSlope(self, input):
        self.maxSlope = input
        self.setShaderInput()

    def regionBounds(self):
        return (self.minHeight, self.maxHeight, self.minSlope, self.maxSlope)

    def setShaderInput(self):
        key = 'region' + str(self.regionNumber) + 'Limits'
        value = self.regionBounds()
        self.terrain.setShaderInput(key, value)
        #logging.info( 'setShaderInput' + str(value))
        #self.terrain.setShader(self.terrain.texturer.shader)

    def resize(self, size):
        self.size = size
        vertical = size[1]- size[0]
        horizontal = size[3]- size[2]
        self.frame.setScale(horizontal / 2, 1, vertical / 2)

    def destroy(self):
        self.frame.destroy()


###############################################################################
#   ShaderDetailControl
###############################################################################
class ShaderDetailControl():
    def __init__(self, x, y, terrain, parent=aspect2d):

        size = 0.5
        self.size = (-size, size, -size, size)
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0),
                                 frameSize=self.size,
                                 pos=(x, 0, y),
                                 parent=parent
                                 )

        self.terrain = terrain
        sg = self.terrain.texturer.shaderGenerator
        #self.normalStregth = terrain.getShaderInput('normalMapStrength').getVector().x
        self.normalStregth = sg.normalMapStrength
        self.normalStregthSlide = SlideControl(0, 0.6, parent=self.frame, range=(0.0001, 10.0), value=self.normalStregth, name="Normal Strength", function=self.setNormalStrength, ysize=1.5, xsize=1.5)

        self.parallaxStrength = sg.parallaxStrength
        self.parallaxStrengthSlide = SlideControl(0, 0.3, parent=self.frame, range=(0.0, sg.parallaxStrength * 5.0), value=self.parallaxStrength, name="Parallax Strength", function=self.setParallaxStrength, ysize=1.5, xsize=1.5)

        self.detailSmallScale = sg.detailSmallScale
        self.detailHugeSlide = SlideControl(0, 0.0, parent=self.frame, range=(0, self.detailSmallScale * 5), value=self.detailSmallScale, name="Small Detail", function=self.setSmallDetail, ysize=1.5, xsize=1.5)

        self.detailBigScale = sg.detailBigScale
        self.detailBigeSlide = SlideControl(0, -0.3, parent=self.frame, range=(0, self.detailBigScale * 5), value=self.detailBigScale, name="BigDetail", function=self.setBigDetail, ysize=1.5, xsize=1.5)

        self.detailHugeScale = sg.detailHugeScale
        self.detailHugeSlide = SlideControl(0, -0.6, parent=self.frame, range=(0, self.detailHugeScale * 5), value=self.detailHugeScale, name="Huge Detail", function=self.setHugeDetail, ysize=1.5, xsize=1.5)

        self.resize(self.size)

    def setNormalStrength(self, input):
        self.normalStregth = input
        self.terrain.setShaderFloatInput("normalMapStrength", self.normalStregth)

    def setParallaxStrength(self, input):
        self.parallaxStrength = input
        self.terrain.setShaderFloatInput("parallaxStrength", self.parallaxStrength)

    def setSmallDetail(self, input):
        self.detailSmallScale = input
        self.terrain.setShaderFloatInput("detailSmallScale", self.detailSmallScale)

    def setBigDetail(self, input):
        self.detailBigScale = input
        self.terrain.setShaderFloatInput("detailBigScale", self.detailBigScale)

    def setHugeDetail(self, input):
        self.detailHugeScale = input
        self.terrain.setShaderFloatInput("detailHugeScale", self.detailHugeScale)

    def resize(self, size):
        self.size = size
        vertical = size[1]- size[0]
        horizontal = size[3]- size[2]
        self.frame.setScale(horizontal / 2, 1, vertical / 2)

    def destroy(self):
        self.frame.destroy()


###############################################################################
#   ShaderMiscellaneousControl
###############################################################################
class ShaderMiscellaneousControl():
    def __init__(self, x, y, terrain, parent=aspect2d):

        size = 0.5
        self.size = (-size, size, -size, size)
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0),
                                 frameSize=self.size,
                                 pos=(x, 0, y),
                                 parent=parent
                                 )

        self.terrain = terrain
        sg = self.terrain.texturer.shaderGenerator

        self.resize(self.size)

        self.occlusionButton = DirectCheckButton(text="Ambient Occlusion", scale=0.15,
                                                 command=self.setAmbientOcclusion, pos=(-0.6, 0, 0.5),
                                                 parent=self.frame)

        self.diffuseButton = DirectCheckButton(text="Disable Diffuse", scale=0.15,
                                                 command=self.setDiffuseTextures, pos=(-0.6, 0, 0.1),
                                                 parent=self.frame)
        self.detail = [0]
        self.detailTexButtons = []
        for number in range(2):
            mypos = (number * 1.5 - 0.6, 0, -0.3)
            button = DirectRadioButton(text='DetailTex'+str(number), variable=self.detail,
                                       value=[number], scale=0.15, pos=mypos,
                                       command=self.switchDetailTexture,
                                       parent=self.frame)
            self.detailTexButtons.append(button)
        for button in self.detailTexButtons:
            button.setOthers(self.detailTexButtons)

        self.fogDensity = sg.fogDensity
        #self.fogDensity = float(self.terrain.getShaderInput('fogDensity').getPtr())
        self.fogDensitySlide = SlideControl(0, -0.7, parent=self.frame, range=(0, 0.1), value=self.fogDensity, name="Fog Density", function=self.setFogDensity, ysize=1.5, xsize=1.5)

    def setDiffuseTextures(self, status):
        if status:
            self.terrain.setShaderFloatInput("debugDisableDiffuse", 1.0)
        else:
            self.terrain.setShaderFloatInput("debugDisableDiffuse", 0.0)

    def setAmbientOcclusion(self, status):
        if status:
            self.terrain.setShaderFloatInput("ambientOcclusion", 1.0)
        else:
            self.terrain.setShaderFloatInput("ambientOcclusion", 0.0)

    def switchDetailTexture(self, status=None):
        if self.detail[0] == 0:
            self.terrain.texturer.shaderGenerator.setDetail(self.terrain.texturer.detailTex)
        if self.detail[0] == 1:
            self.terrain.texturer.shaderGenerator.setDetail(self.terrain.texturer.detailTex2)

    def setFogDensity(self, input):
        self.fogDensity = input
        self.terrain.setShaderFloatInput("fogDensity", self.fogDensity)

    def resize(self, size):
        self.size = size
        vertical = size[1]- size[0]
        horizontal = size[3]- size[2]
        self.frame.setScale(horizontal / 2, 1, vertical / 2)

    def destroy(self):
        self.frame.destroy()


###############################################################################
#   TerrainShaderControl
###############################################################################
class TerrainShaderControl():
    def __init__(self, x, y, terrain, parent=aspect2d):
        self.terrain = terrain

        size = 1.0
        self.size = (-size, size, -size, size)
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0),
                                 frameSize=self.size,
                                 pos=(x, 0, y),
                                 parent=parent
                                 )
        self.buttons = []
        self.v = [0]
        iter = 0
        self.shaderControl = None

        self.addControl('Detail')
        self.addControl('Misc')

        while (self.terrain.getShaderInput('region' + str(iter) + 'Limits').getValueType()):
            iter += 1
            name = 'Region ' + str(iter-1)
            self.addControl(name)

    def addControl(self, name):
        number = len(self.buttons)
        mypos = (number * 0.3 - 0.5, 0, 0.04)

        button = DirectRadioButton(text=name, variable=self.v,
                                   value=[number-2], scale=0.05, pos=mypos,
                                   command=self.switchShaderControl,
                                   parent=self.frame)
        self.buttons.append(button)
        for button in self.buttons:
            button.setOthers(self.buttons)

    # Callback function for radio buttons
    def switchShaderControl(self, status=None):
        if self.shaderControl:
            self.shaderControl.destroy()
        if self.v[0] > -1:
            self.shaderControl = ShaderRegionControl(0, -0.35, self.v[0], self.terrain, parent=self.frame)
        elif self.v[0] == -1:
            self.shaderControl = ShaderMiscellaneousControl(0, -0.35, self.terrain, parent=self.frame)
        elif self.v[0] == -2:
            self.shaderControl = ShaderDetailControl(0, -0.35, self.terrain, parent=self.frame)

    def show(self):
        self.frame.show()

    def hide(self):
        self.frame.hide()

    def setHidden(self, boolean):
        if boolean:
            self.hide()
        else:
            self.show()