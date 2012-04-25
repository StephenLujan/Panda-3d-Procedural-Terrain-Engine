"""
mapeditor.py: This file contains a map editor class for this terrain system

Adapted some code from here
http://tolleybot.wordpress.com/2010/10/03/panda3d-simple-mouse-picking/
"""
__author__ = "Stephen Lujan"

#An event handler test
from direct.task import Task
from panda3d.core import Vec3,Vec4,Point3
from panda3d.core import CollisionRay,CollisionNode,GeomNode,CollisionTraverser
from panda3d.core import CollisionHandlerQueue, CollisionSphere, BitMask32
from terrain import *

class MapEditor():
    def __init__(self, terrain):
        self.terrain = terrain
        self.terrain.setTag('EditableTerrain', '1')
        self.cursor = render.attachNewNode('EditCursor')
        loader.loadModel("models/sphere").reparentTo(self.cursor)
        self.size = 10.0
        self.cursor.setScale(self.size)
        #self.cursor.setSz(self.size / self.terrain.getSz())
        self.cursor.setRenderModeWireframe()
        self.setupMouseCollision()
        self.on = False
        self.disable()

    def enable(self):
        taskMgr.add(self.update, "terrainEditor")
        self.cursor.unstash()

    def disable(self):
        taskMgr.remove("terrainEditor")
        self.cursor.stash()

    def toggle(self, value = None):
        if value == None:
            self.on = not self.on
        else:
            self.on = value
        if self.on:
            self.enable()
        else:
            self.disable()

    def update(self, task):
        self.onMouseTask()
        return Task.cont

    def onMouseTask(self):
        """ """
        #do we have a mouse
        logging.info("onMouseTask")
        if (base.mouseWatcherNode.hasMouse() == False):

            logging.error("no mouse")
            return

        #get the mouse position
        mpos = base.mouseWatcherNode.getMouse()

        #Set the position of the ray based on the mouse position

        if not self.mPickRay.setFromLens(base.camNode, mpos.getX(), mpos.getY()):
            logging.error("point is not acceptable")


        #for this small example I will traverse everything, for bigger projects
        #this is probably a bad idea
        self.mPickerTraverser.traverse(self.terrain)
        logging.info("Mouse pick ray traversing terrain.")

        if (self.mCollisionQueue.getNumEntries() > 0):
            self.mCollisionQueue.sortEntries()
            entry     = self.mCollisionQueue.getEntry(0);
            pickedObj = entry.getIntoNodePath()
            #pickedObj = pickedObj.findNetTag('EditableTerrain')
            if not pickedObj.isEmpty():
                #here is how you get the surface collsion
                pos = entry.getSurfacePoint(render)
                #pos.z *= self.terrain.getSz()
                logging.info(str(pickedObj))
                logging.info(str(pos))
                self.cursor.setPos(pos)
                #handlePickedObject(pickedObj)
            else:
                logging.info("picked object is empty")
        else:
            logging.info("Nothing collided with mouse pick ray")


    def setupMouseCollision(self):
        """ """
        #Since we are using collision detection to do picking, we set it up
        #any other collision detection system with a traverser and a handler
        self.mPickerTraverser = CollisionTraverser()            #Make a traverser
        self.mCollisionQueue  = CollisionHandlerQueue()

        #create a collision solid ray to detect against
        self.mPickRay = CollisionRay()
        #self.mPickRay.setOrigin(base.camera.getPos(render))
        #self.mPickRay.setDirection(render.getRelativeVector(base.camera, Vec3(0,1,0)))

        #create our collison Node to hold the ray
        self.mPickNode = CollisionNode('pickRay')
        self.mPickNode.addSolid(self.mPickRay)

        #Attach that node to the camera since the ray will need to be positioned
        #relative to it, returns a new nodepath
        #well use the default geometry mask
        #this is inefficent but its for mouse picking only

        self.mPickNP = base.camera.attachNewNode(self.mPickNode)

        #well use what panda calls the "from" node.  This is reall a silly convention
        #but from nodes are nodes that are active, while into nodes are usually passive environments
        #this isnt a hard rule, but following it usually reduces processing

        #Everything to be picked will use bit 1. This way if we were doing other
        #collision we could seperate it, we use bitmasks to determine what we check other objects against
        #if they dont have a bitmask for bit 1 well skip them!
        self.mPickNode.setFromCollideMask(GeomNode.getDefaultCollideMask())

        #Register the ray as something that can cause collisions
        self.mPickerTraverser.addCollider(self.mPickNP, self.mCollisionQueue)
        #if you want to show collisions for debugging turn this on
        #self.mPickerTraverser.showCollisions(render)
