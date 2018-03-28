#!/usr/bin/env python3

import cherrypy
import json

import logger
import physical
import settings

import sys
import os

class application(object):
    
    # application variables
    doorStatus = None
    lockStatus = None

    messageContent = None
    defaultMessage = None

    lockServoObject = None
    lockServoPin = None

    reedSwitchPin = 16

    debugEnable = True

    settingList = settings.loadSettings("settings.json");

    def sensorUpdate(self):
        self.doorStatus = physical.readDoorStatus(self.reedSwitchPin, self.debugEnable)

    def resetSensorData(self):
        self.doorStatus = None
        self.lockStatus = None
        self.messageContent = None

    def engageLock(self, overrideSafety, debug):

        self.sensorUpdate()

        if overrideSafety == True:
            physical.lock(self.lockServoObject, self.debugEnable)
            self.lockStatus = True
        else:
            if self.doorStatus == True:
                physical.lock(self.lockServoObject, self.debugEnable)
                self.lockStatus = True
            else:
                logger.log("Door is not closed, so lock will not be engaged")
                logger.log("Either enable override or close door")

    def disengageLock(self, overrideSafety, debug):
        
        self.sensorUpdate()

        # overrideSafety is not needed but added for continuity
        physical.unlock(self.lockServoObject, self.debugEnable)
        self.lockStatus = False

    def assignSettings(self):

        # set application setting values from parsed settings file
        if self.settingList.get("debug") != None:
            self.debugEnable = self.settingList["debug"]

        if self.settingList.get("servo-pin-number") != None:
            self.lockServoPin = self.settingList["servo-pin-number"]
        
        if self.settingList.get("reed-switch-pin") != None:
            self.reedSwitchPin = self.settingList["reed-switch-pin"]

        # fetch objects and initiallize
        if self.lockServoPin != None:
            self.lockServoObject = physical.initServo(self.lockServoPin, self.debugEnable)
            
            # enable event callback
            physical.enableEventLock(self.lockServoPin, self.engageLock, self.debugEnable)

    # http exposed functions

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def unlockdoor(self):
        logger.log("Door unlock signal received")
        self.disengageLock(overrideSafety=False, debug=self.debugEnable)

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def lockdoor(self):
        logger.log("Door lock signal received")
        self.engageLock(overrideSafety=False, debug=self.debugEnable)
        

    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def setmessage(self, motdtext):
        if motdtext != None:
            self.messageContent = motdtext

    @cherrypy.expose
    def infodigest(self):
        
        infoArray = dict()

        infoArray["door-status"] = self.doorStatus
        infoArray["lock-status"] = self.lockStatus
        infoArray["motd"] = self.messageContent
        # not implemented functions
        infoArray["light-status"] = None
        infoArray["temperature"] = None

        # return a formatted JSON reply
        # hopefully this works
        return json.dumps(infoArray)
    
    @cherrypy.expose
    def getdoorstatus(self):
        
        infoArray = dict()

        infoArray["door-status"] = self.doorStatus
        infoArray["lock-status"] = self.lockStatus

        return json.dumps(infoArray)

if __name__ == "__main__":
    
    PATH = os.path.abspath(os.path.dirname(__file__))

    # set default config items
    # allow static files
    conf = dict()

    conf["global"] = { "server.socket_host": "0.0.0.0" }

    conf["/"] = { "tools.staticdir.on": True, "tools.staticdir.dir": PATH, "tools.staticdir.index": "static/status.html" }
    
    appContext = application()
    appContext.assignSettings()

    cherrypy.quickstart(appContext, "/", conf)
