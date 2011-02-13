from direct.gui.DirectGui import *
from direct.gui.DirectGuiBase import DirectGuiWidget
from pandac.PandaModules import TextNode
from pandac.PandaModules import Vec4

class SlideControl():
    def __init__(self, x, y, parent = aspect2d, range=(0,100), value = 50, size = 1, name = "Slider Name", function = 0):

        self.function = function
        #self.extraArgs = extraArgs
        self.size = (-size,size,-size,size)
        self.frame = DirectFrame(parent = parent, frameColor=(0, 0, 0, 0),
                      #frameSize= (-1, 1, -1, 1),
                      pos=(x, 0, y))

        self.slider = DirectSlider(parent = self.frame, range = range, pos = (0,0,0), value=value, pageSize=5, command= self.myFunc)
        self.label = OnscreenText(parent = self.frame, text = name, pos = (-0.7,-0.1), scale = 0.15,fg=(1,0.5,0.5,1),align=TextNode.ACenter,mayChange=0)
        self.value = OnscreenText(parent = self.frame, text = "slider value", pos = (0.7,-0.1), scale = 0.15,fg=(1,0.5,0.5,1),align=TextNode.ACenter,mayChange=1)

        self.resize(self.size)

    def resize(self, size):
        self.size = size
        vertical = size[1]- size[0]
        horizontal = size[3]- size[2]
        self.frame.setScale(horizontal/2, 1, vertical/2)
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

class ShaderRegionControl():
    def __init__(self, x, y, regionNumber, terrain):
        
        size = 0.5
        self.size = (-size,size,-size,size)
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0),
                      frameSize= self.size,
                      pos=(x, 0, y))

        self.regionNumber = regionNumber
        self.terrain = terrain
        self.currentRegion = Vec4(terrain.getShaderInput('region' + str(self.regionNumber) + 'Limits').getVector())
        print "shader control panel for region ", regionNumber, ": ", str(self.currentRegion)

        self.minHeight = self.currentRegion[1]
        self.minHeightSlide = SlideControl(0, 0.6, parent = self.frame, range = (-0.1 * terrain.maxHeight, 1.1 * terrain.maxHeight), value = self.minHeight, name = "Min Height", function = self.setMinHeight)
        self.maxHeight = self.currentRegion[0]
        self.maxHeightSlide = SlideControl(0, 0.2, parent = self.frame, range = (-0.1 * terrain.maxHeight, 1.1 * terrain.maxHeight), value = self.maxHeight, name = "Max Height", function = self.setMaxHeight)
        self.minSlope = self.currentRegion[3]
        self.minSlopeSlide = SlideControl(0, -0.2, parent = self.frame, range = (0,1), value = self.minSlope, name = "Min Slope", function = self.setMinSlope)
        self.maxSlope = self.currentRegion[2]
        self.maxSlopeSlide = SlideControl(0, -0.6, parent = self.frame, range = (0,1), value = self.maxSlope, name = "Max Slope", function = self.setMaxSlope)

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
        return (self.maxHeight, self.minHeight, self.maxSlope, self.minSlope)

    def setShaderInput(self):
        key = 'region' + str(self.regionNumber) + 'Limits'
        value = self.regionBounds()
        self.terrain.setShaderInput(key, value)
        #print 'setShaderInput' + str(value)
        self.terrain.setShader(self.terrain.texturer.shader)

    def resize(self, size):
        self.size = size
        vertical = size[1]- size[0]
        horizontal = size[3]- size[2]
        self.frame.setScale(horizontal/2, 1, vertical/2)

    def destroy(self):
        self.frame.destroy()