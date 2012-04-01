"""
basicfunctions.py: This file contains simple useful functions for Panda3d
"""
__author__ = "Stephen Lujan"

import time

from direct.gui.OnscreenText import OnscreenText
from direct.stdpy import thread
from pandac.PandaModules import TexGenAttrib
from pandac.PandaModules import TextNode
from pandac.PandaModules import WindowProperties

# Function returns the width / height ratio of the window or screen
def getScreenRatio():
    props = WindowProperties(base.win.getProperties())
    return float(props.getXSize()) / float(props.getYSize())

# Function to add instructions and other information along either side
def addText(pos, msg, changeable=False, alignLeft=True, scale=0.05):
    x = -getScreenRatio() + 0.03
    if alignLeft:
        align = TextNode.ALeft
    else:
        align = TextNode.ARight
        x *= -1.0
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1),
                        pos=(x, pos), align=align, scale=scale,
                        mayChange=changeable)

# Function to put title on the screen.
def addTitle(text):
    addText(-0.95, text, False, False, 0.07)

def showFrame():
    for i in range(4):
        base.graphicsEngine.renderFrame()


def threadContinue(sleeptime, lock):
    lock.release()
    time.sleep(sleeptime)
    lock.acquire()

def disableMouse():
    base.disableMouse()
    props = WindowProperties()
    props.setCursorHidden(True)
    base.win.requestProperties(props)

_MOUSELOOK = True
def toggleMouseLook():
    global _MOUSELOOK
    _MOUSELOOK = not _MOUSELOOK
    props = WindowProperties()
    props.setCursorHidden(_MOUSELOOK)
    base.win.requestProperties(props)
    return _MOUSELOOK

def getMouseLook():
    global _MOUSELOOK
    return _MOUSELOOK

def screenShot():
    base.screenshot()
    logging.info('screenshot taken.')

def setResolution(x=800, y=600, fullScreen=False):
    wp = WindowProperties()
    wp.setSize(x, y)
    wp.setFullscreen(fullScreen)
    base.win.requestProperties(wp)
