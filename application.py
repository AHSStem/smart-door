#!/usr/bin/env python3

import cherrypy
import json

import logger
import physical
import settings

import sys
import os
import time

class application(object):
    
    # application variables
    doorStatus = None
    lockStatus = None

    messageContent = None
    defaultMessage = None

    lockServoObject = None
    lockServoPin = None

    reedSwitchPin = None
    doorButtonPin = None

    autolockEnable = None

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

    def doorEvent(self, channel):
        
        # only allow door closing event actions if autolock is enabled
        if self.autolockEnable:
            logger.log("Door closing event detected, sending lock engage in 3 seconds")
            time.sleep(3)
            self.engageLock(overrideSafety=False, debug=self.debugEnable)
        else:
            logger.log("Door closing event detected, but autolock is not enabled")

    def buttonEvent(self, channel):
        
        logger.log("Button press event detected, sending lock engage in 0.5 seconds")
        time.sleep(0.5)
        self.disengageLock(overrideSafety=True, debug=self.debugEnable)

    def assignSettings(self):

        # set application setting values from parsed settings file
        if self.settingList.get("debug") != None:
            self.debugEnable = self.settingList["debug"]

        if self.settingList.get("servo-pin-number") != None:
            self.lockServoPin = self.settingList["servo-pin-number"]
        
        if self.settingList.get("reed-switch-pin") != None:
            self.reedSwitchPin = self.settingList["reed-switch-pin"]
        
        if self.settingList.get("door-button-pin") != None:
            self.doorButtonPin = self.settingList["door-button-pin"]

        if self.settingList.get("default-message") != None:
            self.defaultMessage = self.settingList["default-message"]
        else:
            self.defaultMessage = "message not set"
        
        if self.settingList.get("enable-autolock") != None:
            self.autolockEnable = self.settingList["enable-autolock"]
        else:
            self.autolockEnable = False

        # fetch objects and initiallize
        if self.lockServoPin != None:
            self.lockServoObject = physical.initServo(self.lockServoPin, self.debugEnable)
            
            # setup GPIO pins for read
            physical.initReedSwitch(self.reedSwitchPin, self.debugEnable)
            physical.initDoorButton(self.doorButtonPin, self.debugEnable)

            # enable event callback
            physical.enableDoorEvent(self.reedSwitchPin, self.doorEvent, self.debugEnable)
            physical.enableButtonEvent(self.doorButtonPin, self.buttonEvent, self.debugEnable)

    # http exposed functions

    @cherrypy.expose
    @cherrypy.tools.accept()
    def unlockdoor(self):
        logger.log("Door unlock signal received")
        self.disengageLock(overrideSafety=False, debug=self.debugEnable)

    @cherrypy.expose
    @cherrypy.tools.accept()
    def lockdoor(self):
        logger.log("Door lock signal received")
        self.engageLock(overrideSafety=False, debug=self.debugEnable)
        
    @cherrypy.expose
    @cherrypy.tools.accept(media="text/plain")
    def setmessage(self, motdtext):
        if motdtext != None:
            self.messageContent = motdtext
        return json.dumps({"motd": self.messageContent})

    @cherrypy.expose
    @cherrypy.tools.accept()
    def toggleAutolock(self):
        logger.log("Recieved signal to toggle autolock")
        if self.autolockEnable:
            logger.log("Autolock is enabled - disabling...")
            self.autolockEnable = False
        else:
            logger.log("Autolock is disabled - enabling...")
            self.autolockEnable = True

    @cherrypy.expose
    def infodigest(self):
        
        # update sensors before assembling data
        self.sensorUpdate()

        infoArray = dict()

        infoArray["door-status"] = self.doorStatus
        infoArray["lock-status"] = self.lockStatus
        infoArray["motd"] = self.messageContent
        infoArray["autolock-enabled"] = self.autolockEnable
        # not implemented functions
        infoArray["light-status"] = None
        infoArray["temperature"] = None

        # return a formatted JSON reply
        # hopefully this works
        return json.dumps(infoArray)
    
    @cherrypy.expose
    def getdoorstatus(self):
        
        # update sensors before assembling data
        self.sensorUpdate()

        infoArray = dict()

        infoArray["door-status"] = self.doorStatus
        infoArray["lock-status"] = self.lockStatus

        return json.dumps(infoArray)

    @cherrypy.expose
    def getautolockstatus(self):
        return json.dumps({"autolock-enabled": self.autolockEnable})

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
