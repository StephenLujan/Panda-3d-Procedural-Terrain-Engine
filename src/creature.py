"""
creature.py: This file contains classes for walking characters on the terrain.
There are further implementations for ai, and players.
"""
__author__ = "Stephen Lujan"

import math

from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import NodePath
from pandac.PandaModules import PandaNode
from pandac.PandaModules import Vec2
from pandac.PandaModules import Vec3
import random
from config import *

origin = Vec3(0, 0, 0)

class Walker(NodePath):

    def __init__(self, heightFunction, x=0, y=0):

        NodePath.__init__(self, "Creature")
        self.reparentTo(render)
        self.startPosition = Vec2(x, y)
        z = heightFunction(x, y)
        self.setPos(x, y, z)
        #  movement
        self.acceleration = 25
        self.velocity = Vec3(0, 0, 0)
        self.maxSpeed = 10
        self.speed = 0
        self.maxAngularVelocity = 360
        self.turbo = 1
        self.maxStoppingDistance = self.maxSpeed / self.acceleration * 0.5

        self.body = Actor("models/ralph",
                          {"run":"models/ralph-run",
                          "walk":"models/ralph-walk"})
        self.body.setScale(0.25)
        self.body.reparentTo(self)
        self.heightFunction = heightFunction


    def accelerate(self, desiredVelocity, elapsed):
        acceleration = self.acceleration * elapsed
        deltaV = desiredVelocity - self.velocity
        if deltaV.length() > acceleration:
            deltaV.normalize()
            deltaV *= acceleration
        self.velocity += deltaV
        self.speed = self.velocity.length()
        if self.speed > 0:
            self.isMoving = True
        else:
            self.isMoving = False

    def turnBody(self, desiredHeading, elapsed):
        """
        no angular acceleration...
        its really not that noticeable outside of ragdolls
        """
        heading = self.body.getH()
        maxAngularVelocity = self.maxAngularVelocity * elapsed
        deltaH = desiredHeading - heading

        # Make sure we're taking turning the quick way. If we're turning more
        # than 180.0 we should be turning the other direction.
        if deltaH > 180.0:
            heading += 360.0
            deltaH = desiredHeading - heading
        elif deltaH < -180.0:
            heading -= 360.0
            deltaH = desiredHeading - heading

        #limit turning speed
        if deltaH > maxAngularVelocity:
            deltaH = maxAngularVelocity
        elif deltaH < -maxAngularVelocity:
            deltaH = -maxAngularVelocity
        self.body.setH(heading + deltaH)

    def animate(self):
        # If Ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.
        # reversed walk animation for backward.
        if self.velocity.length > 0:
            if self.isMoving is False:
                self.body.loop("run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.body.stop()
                self.body.pose("walk", 5)
                self.isMoving = False

    def move(self, desiredVelocity, desiredHeading, elapsed):
        # save Ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.
        # this doesn't work now, with collision detection removed, needs fixing
        startpos = self.getPos()

        self.accelerate(desiredVelocity, elapsed)
        self.turnBody(desiredHeading, elapsed)
        self.setPos(startpos + self.velocity * elapsed * self.turbo)
        self.animate()
        self.setZ(self.heightFunction(self.getX(), self.getY()))

    def getMaxArrivalSpeed(self, distance):
        # speed / acc * 0.5 = stopping distance
        # speed = 2 * acc * distance
        return 2 * self.acceleration * distance

class Player(Walker):
    def __init__(self, heightFunction, x=0, y=0):
        Walker.__init__(self, heightFunction, x, y)
        self.controls = {"left":0, "right":0, "forward":0, "back":0, "turbo":0}

    def update(self, elapsed):
        heading = -self.getH()
        direction = 0.0
        self.turbo = 1 + 14 * self.controls["turbo"]

        if self.controls["forward"] == 1:
            if self.controls["right"] != 0:
                #direction = 45.0
                direction = 0.0
            elif self.controls["left"] != 0:
                #direction = 45.0
                direction = 0.0
            elif self.controls["back"] != 0:
                Walker.move(self, Vec3(0, 0, 0), 0, elapsed)
                return
        else:
            if self.controls["right"] != 0:
                direction = -90.0
            elif self.controls["left"] != 0:
                direction = 90.0
            elif self.controls["back"] == 0:
                Walker.move(self, Vec3(0, 0, 0), 0, elapsed)
                return

        # the body is parented to the Player
        # heading will direct the velocity of the Player
        # direction will turn the body relative to the Player
        # the heading of the Player is already altered by the camera
        heading += direction
        desiredVelocity = Vec3(math.sin(heading / 180.0 * math.pi), math.cos(heading / 180.0 * math.pi), 0) * self.maxSpeed
        if self.controls["forward"] == 1:
            desiredVelocity *= -1
        self.move(desiredVelocity, direction, elapsed)

    # records the state of the keyboard
    def setControl(self, control, value):
        self.controls[control] = value


class Ai(Walker):
    def __init__(self, heightFunction, x=0, y=0):
        Walker.__init__(self, heightFunction, x, y)
        self.seekTarget = None
        self.wanderVelocity = None
        self.arrivalRadius = 1

    def update(self, elapsed):
        if self.seekTarget:
            self.seekNP(self.seekTarget, elapsed)
        elif self.wanderVelocity:
            self.wander(elapsed)

    def seekVec(self, target, elapsed):
        desiredVelocity = target - self.getPos()
        desiredVelocity.z = 0

        desiredHeading = math.degrees(math.atan2(desiredVelocity.y, desiredVelocity.x)) + 90

        speed = desiredVelocity.length()
        if speed < self.maxStoppingDistance:
            desiredVelocity.normalize()
            speed = self.getMaxArrivalSpeed(speed)
            desiredVelocity *= speed

        if speed > self.maxSpeed:
            desiredVelocity.normalize()
            desiredVelocity *= self.maxSpeed

        if speed < 1:
            desiredVelocity = Vec3(0, 0, 0)

        self.move(desiredVelocity, desiredHeading, elapsed)

    def seekNP(self, target, elapsed):
        self.seekVec(target.getPos(), elapsed)

    def setSeek(self, target):
        self.seekTarget = target

    def setWander(self, radius=50):
        self.wanderVelocity = Vec2(0, 0)
        self.wanderRadius = radius

    def wander(self, elapsed):
        pos = Vec2(self.getPos().xy)
        r = elapsed * self.maxSpeed * 3
        if (pos - self.startPosition).length() > self.wanderRadius:
            change = self.startPosition - pos
            change.normalize()
            change *= r
        else:
            change = Vec2(random.uniform(-r, r), random.uniform(-r, r))

        desiredVelocity = self.wanderVelocity + change

        desiredVelocity.normalize()
        desiredVelocity *= self.maxSpeed
        self.wanderVelocity = desiredVelocity

        desiredHeading = math.degrees(math.atan2(desiredVelocity.y, desiredVelocity.x)) + 90
        desiredVelocity = Vec3(desiredVelocity.x, desiredVelocity.y, 0)
        #logging.info( desiredVelocity)
        self.move(desiredVelocity, desiredHeading, elapsed)
