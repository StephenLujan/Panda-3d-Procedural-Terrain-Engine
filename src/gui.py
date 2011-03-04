from direct.gui.DirectGui import *
from direct.gui.DirectGuiBase import DirectGuiWidget
from pandac.PandaModules import TextNode
from pandac.PandaModules import Vec4

class SlideControl():
    def __init__(self, x, y, parent = aspect2d, range=(0,100), value = 50, xsize = 1.0, ysize = 1.0, name = "Slider Name", function = 0):

        self.function = function
        #self.extraArgs = extraArgs
        self.size = (-ysize,ysize,-xsize,xsize)
        self.frame = DirectFrame(parent = parent, frameColor=(0, 0, 0, 0),
                      frameSize= self.size,
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
    def __init__(self, x, y, regionNumber, terrain, parent = aspect2d):
        
        size = 0.5
        self.size = (-size,size,-size,size)
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0),
                      frameSize= self.size,
                      pos=(x, 0, y),
                      parent = parent
                      )

        self.regionNumber = regionNumber
        self.terrain = terrain
        self.currentRegion = Vec4(terrain.getShaderInput('region' + str(self.regionNumber) + 'Limits').getVector())
        #print "shader control panel for region ", regionNumber, ": ", str(self.currentRegion)

        self.minHeight = self.currentRegion[1]
        self.minHeightSlide = SlideControl(0, 0.6, parent = self.frame, range = (-0.1 * terrain.maxHeight, 1.1 * terrain.maxHeight), value = self.minHeight, name = "Min Height", function = self.setMinHeight, ysize = 1.5, xsize = 1.5)
        self.maxHeight = self.currentRegion[0]
        self.maxHeightSlide = SlideControl(0, 0.2, parent = self.frame, range = (-0.1 * terrain.maxHeight, 1.1 * terrain.maxHeight), value = self.maxHeight, name = "Max Height", function = self.setMaxHeight, ysize = 1.5, xsize = 1.5)
        self.minSlope = self.currentRegion[3]
        self.minSlopeSlide = SlideControl(0, -0.2, parent = self.frame, range = (0,1), value = self.minSlope, name = "Min Slope", function = self.setMinSlope, ysize = 1.5, xsize = 1.5)
        self.maxSlope = self.currentRegion[2]
        self.maxSlopeSlide = SlideControl(0, -0.6, parent = self.frame, range = (0,1), value = self.maxSlope, name = "Max Slope", function = self.setMaxSlope, ysize = 1.5, xsize = 1.5)

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


class TerrainShaderControl():
    def __init__(self, x, y, terrain, parent = aspect2d):
        self.terrain = terrain

        size = 1.0
        self.size = (-size,size,-size,size)
        self.frame = DirectFrame(frameColor=(0, 0, 0, 0),
                      frameSize= self.size,
                      pos=(x, 0, y),
                      parent = parent
                      )
        self.buttons = []
        self.v = [0]
        iter = 0
        self.shaderControl = ShaderRegionControl(0, -0.35, 0, self.terrain, parent = self.frame)

        while (self.terrain.getShaderInput('region' + str(iter) + 'Limits').getValueType()):
            iter += 1

        total = iter
        iter = 0

        while (self.terrain.getShaderInput('region' + str(iter) + 'Limits').getValueType()):
            button = DirectRadioButton(text='Region ' + str(iter), variable=self.v,
                                       value=[iter], scale=0.05, pos=((iter - total/2) * 0.3, 0, 0.04),
                                       command=self.switchShaderControl,
                                       parent = self.frame)
            self.buttons.append(button)
            iter += 1

        for button in self.buttons:
            button.setOthers(self.buttons)
        
    # Callback function for radio buttons
    def switchShaderControl(self, status=None):
        self.shaderControl.destroy()
        self.shaderControl = ShaderRegionControl(0, -0.35, self.v[0], self.terrain, parent = self.frame)

    def show(self):
        self.frame.show()

    def hide(self):
        self.frame.hide()

    def setHidden(self, boolean):
        if boolean:
            self.hide()
        else:
            self.show()