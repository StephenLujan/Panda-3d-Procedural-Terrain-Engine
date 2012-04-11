"""
terraineditor.py: This file contains a map editor class for this terrain system

Adapted some code from here
http://tolleybot.wordpress.com/2010/10/03/panda3d-simple-mouse-picking/
"""
__author__ = "Stephen Lujan"

#An event handler test
from direct.showbase import DirectObject
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import PointLight
from panda3d.core import Vec3,Vec4,Point3
from panda3d.core import CollisionRay,CollisionNode,GeomNode,CollisionTraverser
from panda3d.core import CollisionHandlerQueue, CollisionSphere, BitMask32
from terrain import *

class MapEditor():
    def __init__(self, terrain):
        self.terrain = terrain
        self.terrain.setTag('EditableTerrain', '1')
        self.cursor = terrain.attachNewNode('EditCursor')
        loader.loadModel("models/sphere").reparentTo(self.cursor)

    def enable(self):
        taskMgr.add(self.update, "terrainEditor")

    def disable(self):
        taskMgr.remove("terrainEditor")

    def update(self):
        self.onMouseTask()

    def onMouseTask(self):
        """ """
        #do we have a mouse
        if (self.mouseWatcherNode.hasMouse() == False):
                return

        #get the mouse position
        mpos = base.mouseWatcherNode.getMouse()

        #Set the position of the ray based on the mouse position

        self.mPickRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())

        #for this small example I will traverse everything, for bigger projects
        #this is probably a bad idea
        self.mPickerTraverser.traverse(self.render)

        if (self.mCollisionQue.getNumEntries() > 0):
                self.mCollisionQue.sortEntries()
                entry     = self.mCollisionQue.getEntry(0);
                pickedObj = entry.getIntoNodePath()

                pickedObj = pickedObj.findNetTag('MyObjectTag')
                if not pickedObj.isEmpty():
                        #here is how you get the surface collsion
                        pos = entry.getSurfacePoint(self.render)
                        print pickedObj
                        #handlePickedObject(pickedObj)

    def setupMouseCollision(self):
        """ """
        #Since we are using collision detection to do picking, we set it up
        #any other collision detection system with a traverser and a handler
        self.mPickerTraverser = CollisionTraverser()            #Make a traverser
        self.mCollisionQue    = CollisionHandlerQueue()

        #create a collision solid ray to detect against
        self.mPickRay = CollisionRay()
        self.mPickRay.setOrigin(self.camera.getPos(self.render))
        self.mPickRay.setDirection(render.getRelativeVector(camera, Vec3(0,1,0)))

        #create our collison Node to hold the ray
        self.mPickNode = CollisionNode('pickRay')
        self.mPickNode.addSolid(self.mPickRay)

        #Attach that node to the camera since the ray will need to be positioned
        #relative to it, returns a new nodepath
        #well use the default geometry mask
        #this is inefficent but its for mouse picking only

        self.mPickNP = self.camera.attachNewNode(self.mPickNode)

        #well use what panda calls the "from" node.  This is reall a silly convention
        #but from nodes are nodes that are active, while into nodes are usually passive environments
        #this isnt a hard rule, but following it usually reduces processing

        #Everything to be picked will use bit 1. This way if we were doing other
        #collision we could seperate it, we use bitmasks to determine what we check other objects against
        #if they dont have a bitmask for bit 1 well skip them!
        self.mPickNode.setFromCollideMask(GeomNode.getDefaultCollideMask())

        #Register the ray as something that can cause collisions
        self.mPickerTraverser.addCollider(self.mPickNP, self.mCollisionQue)
        #if you want to show collisions for debugging turn this on
        #self.mPickerTraverser.showCollisions(self.render)
