from config import *
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletPlaneShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletWorld
from panda3d.core import NodePath
from panda3d.core import RigidBodyCombiner
from panda3d.core import Vec3
from random import randint
from random import random

class TerrainPhysicsDemo2():
    """Modified from ODE demo and Bullet demo."""
    def __init__(self, world, spawnNP):
        self.running = False
        self.world = world
        rbc = RigidBodyCombiner("rbc")
        self.rbcnp = NodePath(rbc)
        self.rbcnp.reparentTo(render)
        self.NrObjectToDrop = 10
        self.spawnNP = spawnNP
        self.objects = []
        self.model = loader.loadModel('models/box.egg')
        self.model.flattenLight()
        self.shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))

    def start(self):
        """Drop Rectangles"""
        # add objects one by one
        if self.running:
            return
        self.running = True
        self.newObjects = 0
        taskMgr.doMethodLater(0.5, self.runTask, "myDemo")

    def runTask(self, task):
        if self.demoContinue():
            return task.done
        return task.again

    def demoContinue(self):
        if self.newObjects < self.NrObjectToDrop:

            node = BulletRigidBodyNode('Box')
            node.setMass(1.0)
            node.addShape(self.shape)
            np = self.rbcnp.attachNewNode(node)
            np.setPos(self.spawnNP.getPos(render))
            np.setHpr(randint(-45, 45), randint(-45, 45), randint(-45, 45))
            self.world.attachRigidBody(node)

            bNP = self.model.copyTo(np)
            #bNP.setPos(self.spawnNP.getPos())
            #bNP.setColor(random(), random(), random(), 1)
            #bNP.setHpr(randint(-45, 45), randint(-45, 45), randint(-45, 45))
            #self.setUntextured(bNP)
            #bNP.setTexureOff()
            #np.setScale(10)
            np.flattenStrong()

            self.objects.append(np)
            self.newObjects += 1
            self.rbcnp.node().collect()

        if self.newObjects < self.NrObjectToDrop:
            return False
        else:
            self.running = False
            return True


class TerrainPhysicsDemo():
    """Modified from Bullet sample."""
    def __init__(self, world, spawnNP):

        ## Plane
        #shape = BulletPlaneShape(Vec3(0, 0, 1), 1)
        #node = BulletRigidBodyNode('Ground')
        #node.addShape(shape)
        #np = render.attachNewNode(node)
        #np.setPos(0, 0, -2)
        #world.attachRigidBody(node)
        self.world = world
        self.spawnNP = spawnNP

    def start(self):
        # Boxes
        model = loader.loadModel('models/box.egg')
        model.setPos(-0.5, -0.5, -0.5)
        model.flattenLight()
        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        for i in range(10):
            node = BulletRigidBodyNode('Box')
            node.setMass(1.0)
            node.addShape(shape)
            np = render.attachNewNode(node)
            np.setPos(self.spawnNP.getPos(render) + Vec3(0, 0, 2 + i * 2))
            self.world.attachRigidBody(node)
            model.copyTo(np)
        logging.info("Box test placed at " + str(self.spawnNP.getPos()))


class TerrainPhysics():
    def __init__(self, ):
        # World
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))


    def setup(self, terrain, player):
        """Bullet has to be started before some things in the program to avoid crashes."""
        self.terrain = terrain
        self.player = player

        # Demo
        spawn = player.attachNewNode("spawnPoint")
        spawn.setPos(0, -5, 7)
        self.demo = TerrainPhysicsDemo2(self.world, spawn)
        taskMgr.add(self.update, 'physics')

    def test(self):
        self.demo.start()

    def update(self, task):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont