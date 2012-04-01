"""
splashCard.py:  The SplashCard will hide the scene and present a simple message
while the scene is being prepared.

Borrowed some code from Astelix from the Panda3d forum. Thanks Astelix.
"""
__author__ = "Stephen Lujan"

from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import TransparencyAttrib
from pandac.PandaModules import Vec4
from config import *

class SplashCard(object):
    '''this class shows up a splash message'''
    #------------------------------------------------------------
    #
    def __init__(self, image, backgroundColor):
        self.loadingimage = OnscreenImage(image, color=(1, 1, 1, 1), scale=.5, parent=aspect2d)
        self.loadingimage.setTransparency(1)
        # this image will be on top of all therefore we use setBin 'fixed' and with the higher sort value
        self.loadingimage.setBin("fixed", 20)

        self.curtain = OnscreenImage('textures/curtain.png', parent=render2d, color=backgroundColor)
        self.curtain.setTransparency(1)
        # this is to set it below the loading panel
        self.curtain.setBin("fixed", 10)

        # the loading panel faders
        self.loadingOut = self.loadingimage.colorInterval(1, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1))
        # the black curtain faders
        self.openCurtain = self.curtain.colorScaleInterval(1, Vec4(1, 1, 1, 0), Vec4(1, 1, 1, 1))
        for i in range(4):
            base.graphicsEngine.renderFrame()
    #------------------------------------------------------------
    #
    def destroy(self):
        Sequence(self.loadingOut, self.openCurtain).start()
        #Sequence(self.openCurtain).start()
        #self.loadingimage.destroy()
        #self.curtain.destroy()