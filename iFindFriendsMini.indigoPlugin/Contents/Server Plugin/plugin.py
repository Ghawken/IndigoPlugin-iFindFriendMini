#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
FindFriendsMini
Authors: See (repo)

Logons on to icloud account and access friends information for creation of indigo Devices

Enormously based on FindiStuff by Chameleon and GhostXML by DaveL17

"""

# Stock imports

global MajorProblem

MajorProblem = 0
startingUp = False

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except Exception as e:
    pass
    #o.server.log(u'error in import locales')

import sys
import math
import logging
#import OpenSSL
import WazeRouteCalculator

import time as t
import json
try:
    import indigo
except ImportError:
    MajorProblem = 2  #1 to restart, 2 to disable
    pass

try:
    from pyicloud import PyiCloudService
    #from pyicloud.exceptions import PyiCloudFailedLoginException
    #import moduledoesntexisit
    from pyicloud.exceptions import (
        PyiCloudFailedLoginException,
        PyiCloudAPIResponseException,
        PyiCloudNoDevicesException,
        PyiCloud2SARequiredException,
        PyiCloudServiceNotActivatedException,
    )
# try:
#     from custompyicloud.custompyicloud import PyiCloudService
#     #from pyicloud.exceptions import PyiCloudFailedLoginException
#     #import moduledoesntexisit
#     from custompyicloud.custompyicloud import (
#         PyiCloudException,
#         PyiCloudAPIResponseException,
#         PyiCloudServiceNotActivatedException,
#         PyiCloudFailedLoginException,
#         PyiCloud2SARequiredException,
#         PyiCloudNoStoredPasswordAvailableException,
#         PyiCloudNoDevicesException
#     )

except Exception as e:
    MajorProblem =2
    errortext = str(e)
    indigo.server.log(u"{0:=^130}".format(""), isError=True)
    indigo.server.log(u'Returned Error:'+str(e), isError=True)
    indigo.server.log(u"{0:=^130}".format(""), isError=True)
    indigo.server.log("-- FATAL ERROR - Cannot find pyicloud or cannot load pyicloud or dependency.", isError=True)


    if 'pytz' in errortext:
        indigo.server.log('Missing pytz package.  Please Follow Below instructions. (Once only needed)', isError=True)
        indigo.server.log(u"{0:=^130}".format(""), isError=True)
        try:
            #import pip
            t.sleep(5)
            indigo.server.log(u"{0:=^130}".format(""), isError=True)
            indigo.server.log('Open Terminal Window and type.', isError=True)
            indigo.server.log('sudo easy_install pip', isError=True)
            indigo.server.log('& then.  [Both followed by enter]', isError=True)
            indigo.server.log('sudo pip install pytz', isError=True)
            indigo.server.log(u"{0:=^130}".format(""), isError=True)
            indigo.server.log('Plugin will restart in 3 minutes', isError=True)
            #pip.main(['install', 'microcache'])
            t.sleep(180)
            indigo.server.log('Restarting Plugin...', isError=True)
            indigo.server.log(u"{0:=^130}".format(""), isError=True)
            t.sleep(2)
            MajorProblem = 1

        except Exception as b:
            indigo.server.log(u'Major Problem. Please contact developer.  Error:'+str(b), isError=True)
            MajorProblem = 2
            pass

    if 'six' in errortext:
        indigo.server.log('Missing six package.  Please Follow Below instructions. (Once only needed)', isError=True)
        indigo.server.log(u"{0:=^130}".format(""), isError=True)
        try:
            #import pip
            t.sleep(5)
            indigo.server.log(u"{0:=^130}".format(""), isError=True)
            indigo.server.log('Open Terminal Window and type.', isError=True)
            indigo.server.log('sudo easy_install pip', isError=True)
            indigo.server.log('& then.  [Both followed by enter]', isError=True)
            indigo.server.log('sudo pip install six', isError=True)
            indigo.server.log(u"{0:=^130}".format(""), isError=True)
            indigo.server.log('Plugin will restart in 3 minutes', isError=True)
            #pip.main(['install', 'microcache'])
            t.sleep(180)
            indigo.server.log('Restarting Plugin...', isError=True)
            indigo.server.log(u"{0:=^130}".format(""), isError=True)
            t.sleep(2)
            MajorProblem = 1

        except Exception as b:
            indigo.server.log(u'Major Problem. Please contact developer.  Error:'+str(b), isError=True)
            MajorProblem = 2
            pass
    else:
        indigo.server.log(u"{0:=^130}".format(""), isError=True)
        indigo.server.log(u'Major Problem. Please contact developer.  Error:' + str(e), isError=True)
        MajorProblem = 2
        pass
# Now the HTTP and Compatibility libraries
#indigo.server.log(u"{0:=^130}".format(""), isError=True)

try:
    import requests
except:
    indigo.server.log("Note: requests.py must be installed for this plugin to operate.  Indigo 7 ONLY.  See the forum",isError=True)
    indigo.server.log(
        "Alternatively - check the name of the plugin in the Plugins folder.  Is is FindFriendsMini.pluginIndigo"
        "or FindFriendsMini(1).pluginIndigo?  Make sure that all FindFriendsMini files are deleted from Downloads"
        "before downloading the latest versions", isError=True)

# Date and time libraries
import time

try:
    import pydevd
except ImportError:
    pass

# try:
#     # from googlemaps import googlemaps
#     # from googlemaps.exceptions import (
#     #     ApiError,
#     #     TransportError,
#     #     HTTPError,
#     #     Timeout
#     # )
# except Exception as e:
#     indigo.server.log(u"{0:=^130}".format(""), isError=True)
#     indigo.server.log(u'Error Importing Googlemaps.  Error:'+str(e), isError=True)
#     indigo.server.log(u"{0:=^130}".format(""), isError=True)

import webbrowser
import os
import logging
import datetime
import glob
#from ghpu import GitHubPluginUpdater

global accountOK
#global self.appleAPI

# Custom imports
#import iterateXML

__author__ = u"GlennNZ"
__build__ = u""
__copyright__ = u"There is no copyright for the code base."
__license__ = u"MIT"
__title__ = u"FindFriendsMini Plugin for Indigo Home Control"
__version__ = u"0.4.5"

# Establish default plugin prefs; create them if they don't already exist.
kDefaultPluginPrefs = {
    u'configMenuServerTimeout': "5",  # Server timeout limit.
    u'showDebugInfo': False,  # Verbose debug logging?
    u'showDebugLevel': "20",  # Low, Medium or High debug output.
    u'updaterEmail': "",  # Email to notify of plugin updates.
    u'updaterEmailsEnabled': False  # Notification of plugin updates wanted.
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        """ docstring placeholder """


        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.startingUp = True
        apleAPI = None
        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False
        self.prefsUpdated = False
        self.logger.info(u"")
        self.logger.info(u"{0:=^130}".format(" Initializing New Plugin Session "))
        self.logger.info(u"{0:<30} {1}".format("Plugin name:", pluginDisplayName))
        self.logger.info(u"{0:<30} {1}".format("Plugin version:", pluginVersion))
        self.logger.info(u"{0:<30} {1}".format("Plugin ID:", pluginId))
        self.logger.info(u"{0:<30} {1}".format("Indigo version:", indigo.server.version))
        self.logger.info(u"{0:<30} {1}".format("Python version:", sys.version.replace('\n', '')))
        self.logger.info(u"{0:<30} {1}".format("Python Directory:", sys.prefix.replace('\n', '')))
        self.logger.info(u"{0:<30} {1}".format("Major Problem equals: ", MajorProblem))
        self.logger.info(u"{0:=^130}".format(""))

        self.iprefDirectory = '{}/Preferences/Plugins/com.GlennNZ.indigoplugin.FindFriendsMini'.format(indigo.server.getInstallFolderPath())
        #Change to logging
        pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')
        self.plugin_file_handler.setFormatter(pfmt)

        try:
            self.logLevel = int(self.pluginPrefs[u"showDebugLevel"])
        except:
            self.logLevel = logging.INFO

        ## Create new Log File
        try:
            self.newloggerhandler = logging.FileHandler(u"{0}/Logs/com.GlennNZ.indigoplugin.FindFriendsMini/FFM-GeofenceData.log".format(
            indigo.server.getInstallFolderPath()))
            formatter = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s',
                                     datefmt='%Y-%m-%d %H:%M:%S')
            self.newloggerhandler.setFormatter(formatter)
            self.newlogger = logging.getLogger('FindFriends-GeofenceData')
            self.newlogger.setLevel(logging.DEBUG)
            self.newlogger.addHandler(self.newloggerhandler)
        except:
            self.logger.exception(u'Error in Debug New Log Setup')

        self.indigo_log_handler.setLevel(self.logLevel)
        self.logger.debug(u"logLevel = " + str(self.logLevel))
        self.triggers = {}

        self.appleAPI = None

        self.debugicloud = self.pluginPrefs.get('debugicloud', False)
        self.debugLevel = int(self.pluginPrefs.get('showDebugLevel', 20))
        self.debugmaps = self.pluginPrefs.get('debugmaps', False)
        self.debuggeofence   = self.pluginPrefs.get('debuggeofence', False)
        self.debugdistance = self.pluginPrefs.get('debugdistance', False)
        self.logFile = u"{0}/Logs/com.GlennNZ.indigoplugin.FindFriendsMini/plugin.log".format( indigo.server.getInstallFolderPath())

        if self.debuggeofence:
            self.newlogger.info(u"")
            self.newlogger.info(u"{0:=^130}".format(" Initializing New Plugin Session "))
            self.newlogger.info(u"{0:<30} {1}".format("Plugin name:", pluginDisplayName))
            self.newlogger.info(u"{0:<30} {1}".format("Plugin version:", pluginVersion))
            self.newlogger.info(u"{0:<30} {1}".format("Plugin ID:", pluginId))
            self.newlogger.info(u"{0:<30} {1}".format("Indigo version:", indigo.server.version))
            self.newlogger.info(u"{0:<30} {1}".format("Python version:", sys.version.replace('\n', '')))
            self.newlogger.info(u"{0:<30} {1}".format("Python Directory:", sys.prefix.replace('\n', '')))
            self.newlogger.info(u"{0:<30} {1}".format("Major Problem equals: ", MajorProblem))
            self.newlogger.info(u"{0:=^130}".format(""))


        self.TwoFAverified = False

        self.configMenuTimeCheck = int(self.pluginPrefs.get('configMenuTimeCheck', "5"))
        #self.updater = indigoPluginUpdateChecker.updateChecker(self, "http://")
        self.updaterEmailsEnabled = self.pluginPrefs.get('updaterEmailsEnabled', False)

        self.updateFrequency = float(self.pluginPrefs.get('updateFrequency', "24")) * 60.0 * 60.0
        self.next_update_check = time.time()
        self.configVerticalMap = self.pluginPrefs.get('verticalMap', "600")
        self.useMaps = self.pluginPrefs.get('useMaps',False)
        self.mapType = self.pluginPrefs.get('mapType', "openstreetmap")
        if self.mapType == None:
            self.useMaps = False
        self.configHorizontalMap = self.pluginPrefs.get('horizontalMap', "600")
        self.configZoomMap = self.pluginPrefs.get('ZoomMap', "15")
        self.datetimeFormat = self.pluginPrefs.get('datetimeFormat','%c')
        self.googleAPI = self.pluginPrefs.get('googleAPI','')
        self.BingAPI = self.pluginPrefs.get('BingAPI','')

        self.wazeRegion = self.pluginPrefs.get('wazeRegion','EU')
        self.wazeUnits = self.pluginPrefs.get('wazeUnits','km')
        self.deviceNeedsUpdated = ''
        self.openStore = self.pluginPrefs.get('openStore',False)
        self.requires2FA = False   ## If account requires another set to be done, will change from True - False
        self.requires2SA = False


        if MajorProblem > 0:
            plugin = indigo.server.getPlugin('com.GlennNZ.indigoplugin.FindFriendsMini')

            if MajorProblem == 1:
                self.logger.error(u'Major Problem:  Restarting Plugin...')
                if plugin.isEnabled():
                    plugin.restart(waitUntilDone=False)
                self.sleep(1)
            if MajorProblem == 2:
                self.logger.error(u"{0:=^130}".format(""))
                self.logger.error(u"{0:=^130}".format(""))
                self.logger.error(u'Major Problem:   Please Disable Plugin.  Now Sleeping.  Please contact Developer.')
                self.logger.error(u"{0:=^130}".format(""))
                self.logger.error(u"{0:=^130}".format(""))
                if plugin.isEnabled():
                    # Can't disabled
                    # Can Sleep Forever Though
                    #plugin.disable()

                    self.sleep(86400)

        self.pluginIsInitializing = False

    ###
    ###  Update ghpu Routines.


    def pluginstoreUpdate(self):
        iurl = 'http://www.indigodomo.com/pluginstore/139/'
        self.browserOpen(iurl)

    #####

    def __del__(self):
        """ docstring placeholder """


        self.logger.debug(u"__del__ method called.")

        indigo.PluginBase.__del__(self)

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        """ docstring placeholder """


        self.logger.debug(u"closedPrefsConfigUi() method called.")

        if userCancelled:
            self.logger.debug(u"User prefs dialog cancelled.")

        if not userCancelled:
            self.debug = valuesDict.get('showDebugInfo', False)
            self.debugLevel = int(valuesDict.get('showDebugLevel', "20"))
            self.debugicloud = valuesDict.get('debugicloud', False)
            self.debugmaps = valuesDict.get('debugmaps', False)
            self.debuggeofence = valuesDict.get('debuggeofence', False)
            self.debugdistance = valuesDict.get('debugdistance', False)
            self.datetimeFormat = valuesDict.get('datetimeFormat', '%c')
            self.configVerticalMap = valuesDict.get('verticalMap', "600")
            self.useMaps = valuesDict.get('useMaps',False)
            self.mapType = self.pluginPrefs.get('mapType', "openstreetmap")
            self.configHorizontalMap = valuesDict.get('horizontalMap', "600")
            self.configZoomMap = valuesDict.get('ZoomMap', "15")
            self.datetimeFormat = valuesDict.get('datetimeFormat', '%c')
            self.googleAPI = valuesDict.get('googleAPI', '')
            self.BingAPI = valuesDict.get('BingAPI','')
            self.openStore = valuesDict.get('openStore', False)
            self.updateFrequency = float(valuesDict.get('updateFrequency', "24")) * 60.0 * 60.0
            # If plugin config menu closed update the time for check.  Will apply after first change.
            self.configMenuTimeCheck = int(valuesDict.get('configMenuTimeCheck', "5"))
            self.prefsUpdated = True

            try:
                self.logLevel = int(valuesDict[u"showDebugLevel"])
            except:
                self.logLevel = logging.INFO
            self.indigo_log_handler.setLevel(self.logLevel)

            self.logger.debug(u"logLevel = " + str(self.logLevel))
            self.logger.debug(u"User prefs saved.")
            self.logger.debug(u"Debugging on (Level: {0})".format(self.debugLevel))



        return True

    def deviceStartComm(self, dev):
        """ docstring placeholder """
        self.logger.debug(u"deviceStartComm() method called.")
        self.logger.debug(u'Starting FindFriendsMini device: '+str(dev.name)+' and dev.id:'+str(dev.id)+ ' and dev.type:'+str(dev.deviceTypeId))
        # Update statelist in case any updates/changes
        dev.stateListOrDisplayStateIdChanged()

        if dev.deviceTypeId=='FindFriendsGeofence':
            stateList = [
                #{'key': 'friendsInRange', 'value': 0},
                #{'key': 'lastArrivaltime', 'value': ''},
                #{'key': 'lastDeptime', 'value': ''},
                #{'key': 'lastArrivaltimestamp', 'value': ''},
                #{'key': 'lastDeptimestamp', 'value': ''},
                #{'key': 'minutessincelastArrival', 'value': 0},
                #{'key': 'minutessincelastDep', 'value': 0},
                {'key': 'occupied', 'value': False},
                {'key': 'deviceIsOnline', 'value': False, 'uiValue':'Waiting'}]

            #self.logger.debug(str(stateList))
            dev.updateStatesOnServer(stateList)

        if dev.deviceTypeId == 'FindFriendsFriend':
            stateList = [
                {'key': 'id', 'value':''},
                {'key': 'status', 'value': ''},
                {'key': 'locationStatus', 'value': ''},
                {'key': 'batteryStatus', 'value': ''},
                {'key': 'locationTimestamp', 'value': ''},
                {'key': 'timestamp', 'value': ''},
                {'key': 'altitude', 'value': ''},
        #        {'key':'isHome','value':False,
                {'key': 'homeDistance', 'value': 0},
                {'key': 'homeTime', 'value': 0},
                {'key': 'otherDistance', 'value': 0},
                {'key': 'otherTime', 'value': 0},
                {'key': 'homeDistanceText', 'value': 'unknown'},
                {'key': 'homeTimeText', 'value': 'unknown'},
                {'key': 'otherDistanceText', 'value': 'unknown'},
                {'key': 'otherTimeText', 'value': 'unknown'},
                {'key': 'googleMapUrl', 'value': ''},
                {'key': 'labels', 'value': ''},
                {'key': 'longitude', 'value': 'unknown'},
                {'key': 'horizontalAccuracy', 'value': ''},
                {'key': 'address', 'value': ''},
                {'key': 'latitude', 'value': 'unknown'},
                {'key': 'mapUpdateNeeded', 'value': True}
                ]

            #self.logger.debug(str(stateList))
            dev.updateStatesOnServer(stateList)
        elif dev.deviceTypeId=="myDevice":
            stateList = [
                {'key': 'id', 'value': ''},
                {'key': 'status', 'value': ''},
                {'key': 'batteryStatus', 'value': ''},
                {'key': 'locationTimestamp', 'value': ''},
                {'key': 'timestamp', 'value': ''},
                {'key': 'altitude', 'value': ''},
                {'key': 'homeDistance', 'value': 0},
                {'key': 'homeTime', 'value': 0},
          #      {'key': 'isHome', 'value': False,
                {'key': 'batteryCharge', 'value': 0},
                {'key': 'otherDistance', 'value': 0},
                {'key': 'otherTime', 'value': 0},
                {'key': 'homeDistanceText', 'value': 'unknown'},
                {'key': 'homeTimeText', 'value': 'unknown'},
                {'key': 'otherDistanceText', 'value': 'unknown'},
                {'key': 'otherTimeText', 'value': 'unknown'},
                {'key': 'googleMapUrl', 'value': ''},
                {'key': 'longitude', 'value': 'unknown'},
                {'key': 'horizontalAccuracy', 'value': ''},
                {'key': 'address', 'value': ''},
                {'key': 'latitude', 'value': 'unknown'},
                {'key': 'devSummary', 'value': 'Offline'},
                {'key': 'mapUpdateNeeded', 'value': True},

            ]
            #self.logger.debug(str(stateList))
            dev.updateStatesOnServer(stateList)

        self.prefsUpdated = True
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Waiting")
        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

    def deviceStopComm(self, dev):
        """ docstring placeholder """

        self.logger.debug(u"deviceStopComm() method called.")
        self.logger.debug(u"Stopping FindFriendsMini device: {0}".format(dev.name))
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Disabled")
        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

        # =============================================================

    def actionrefreshdata(self, action):

        self.logger.debug(u"actionrefreshdata() method called.")
        self.refreshData()
        self.sleep(5)
        self.checkGeofence()
        self.sleep(2)
        self.checkHomeOther()
        return

    def actionrefreshmaps(self, action):

        self.logger.debug(u"actionrefreshmaps() method called.")
        for dev in indigo.devices.iter('self.FindFriendsFriend'):
            dev.updateStateOnServer('mapUpdateNeeded', value=True)

        self.refreshData()

        return


    def openGoogleUrl(self, pluginAction, device):
        self.logger.debug(u'openGoogleUrl Run')
        try:
            page = '<a href="'+str(device.states['googleMapUrl'])+'"></a>'

            return page
        except:
            self.looger.exception(u'Issue with OpenGoogleURL')
            return

    def menuRefresh(self):
        self.logger.debug(u'menuRefresh called.')
        self.actionrefreshdata('nil')
        return

    def updateVar(self, name, value):
        self.logger.debug(u'updatevar run.')
        if not ('FindFriendsMini' in indigo.variables.folders):
            # create folder
            folderId = indigo.variables.folder.create('FindFriendsMini')
            folder = folderId.id
        else:
            folder = indigo.variables.folders.getId('FindFriendsMini')

        if name not in indigo.variables:
            NewVar = indigo.variable.create(name, value=value, folder=folder)
        else:
            indigo.variable.updateValue(name, value)
        return

    def changeInterval(self, action):
        self.logger.debug(u"change interval() method called.")
        # If plugin config menu closed update the time for check.  Will apply after first change.
        self.configMenuTimeCheck = int(action.props.get('configMenuTimeCheck', "5"))
        self.prefsUpdated = True
        return

    def playSound(self, action):
        try:
            self.logger.debug(u"PlaySound method called.")
            # If plugin config menu closed update the time for check.  Will apply after first change.
            targetDevice = action.props.get('targetDevice', "")
            targetSubject = action.props.get('subject',"Indigo Alert")
            self.logger.debug("targetDevice: "+str(targetDevice))
            if targetDevice =="":
                self.logger.info("Please Enter a Device.")
                return

            devicetargets = self.appleAPI.devices
            for devices in devicetargets:
                # self.logger.error(str(devices))
                # self.logger.error(devices['id'])
                # self.logger.error(devices.status())
                # self.logger.error(devices.location())
                if str(targetDevice) == str(devices['id']):
                    devices.play_sound(subject=targetSubject)

            return
        except Exception as e:
            self.logger.exception(u"Exception in PlaySound")

    def displayMessage(self, action):
        try:
            self.logger.debug(u"DisplayMessage method called.")
            # If plugin config menu closed update the time for check.  Will apply after first change.
            targetDevice = action.props.get('targetDevice', "")
            targetSubject = action.props.get('subject',"Indigo Alert")
            soundenabled = action.props.get('sound',False)
            targetMessage = action.props.get('message',"")
            self.logger.debug("targetDevice: "+str(targetDevice))
            if targetDevice =="":
                self.logger.info("Please Enter a Device.")
                return

            devicetargets = self.appleAPI.devices
            for devices in devicetargets:
                # self.logger.error(str(devices))
                # self.logger.error(devices['id'])
                # self.logger.error(devices.status())
                # self.logger.error(devices.location())
                if str(targetDevice) == str(devices['id']):
                    devices.display_message(subject=targetSubject, message=targetMessage, sounds=soundenabled)

            return
        except Exception as e:
            self.logger.exception(u"Exception in PlaySound")

    def runConcurrentThread(self):
        """ docstring placeholder """
        self.logger.debug(u"ronConCurrentThread() method called.")
        #secondsbetweencheck = 60*self.configMenuTimeCheck
        self.logger.debug(u"secondsbetween Check Equal:"+str(60*self.configMenuTimeCheck))
        # Change to time based looping with second checking.  Allowing to update Geofences minutely and any config changes to be immediately registered
        while self.pluginIsShuttingDown == False:
        # Shutdown nicely
            self.logger.debug(u'ronConcurrrent loop: pluginshuttingdown=False Loop Running.')
            currenttimenow = time.time()
            nextloopdue = time.time() + 5  # currenttime plus 5 seconds when next loop is due.  Will need to reset with config changes.
            self.prefsUpdated = False
            self.sleep(0.5)
            updateGeofencedue = time.time() + 60 # Geofence update due in 65 seconds # should be reset below

            while self.prefsUpdated == False:
                if int(updateGeofencedue-time.time()) == 0:
                    self.logger.debug(u'ronConcurrrent internal loop: self.prefsUpdated False: Next Update:'+str(int(time.time()-nextloopdue))+' and updateGeofenceDue:'+str(int(updateGeofencedue-time.time())))
                # Update Plugin Frequency Loop

                # Update Loop Check.  Checks Devices and GeoFences.
                if time.time() > nextloopdue:
                    try:
                    #self.sleep()
                        if self.requires2FA == False:
                            self.logger.debug(u'ronConcurrrent loop: Running Update:')
                            self.refreshData()
                            self.sleep(2)
                            self.checkGeofence()   #Check distances etc of GeoFences
                            self.sleep(2)
                            self.checkHomeOther()
                            nextloopdue = time.time() + int(60 * self.configMenuTimeCheck)
                            #reset Geofence time update as done above
                            updateGeofencedue = time.time() + 60
                            self.logger.debug(u'ronConcurrrent loop: Next Update due (seconds):'+str(int(time.time()-nextloopdue)))
                        else:
                            self.logger.info(u"Account requires verification within Plugin Config.")
                            nextloopdue = time.time() + int(60 * self.configMenuTimeCheck)
                            updateGeofencedue = time.time() + 60
                            self.triggerCheck2fa()
                    except:
                        self.logger.debug(u'Error within RunConcurrentLoop Update cycle')
                        nextloopdue = time.time() + int(60 * self.configMenuTimeCheck)
                # Move to time for Geofences - so always in sync
                if time.time() > updateGeofencedue:
                    self.updateGeofencetime()
                    # after first loops run and 60 seconds has passed, we will be here
                    # set end of startingUp now.
                    self.startingUp = False
                    # add 60 seconds
                    updateGeofencedue = time.time() + 60

                self.sleep(1)


        self.logger.debug(u'Exiting self.pluginIsShuttingDown Loop.')


    def shutdown(self):
        """ docstring placeholder """


        self.logger.debug(u"Shutting down FindFriendsMini. shutdown() method called")
        self.pluginIsShuttingDown = True

    def startup(self):
        """ docstring placeholder """


        self.logger.debug(u"Starting FindFriendsMini. startup() method called.")
        #self.updater = GitHubPluginUpdater(self)
        # Set self.appleAPI account as not verified on start of startup
        accountOK = False
        MAChome = os.path.expanduser("~") + "/"
        folderLocation = MAChome + "Documents/Indigo-iFindFriendMini/"
        if not os.path.exists(folderLocation):
            os.makedirs(folderLocation)

        if not os.path.exists(self.iprefDirectory):
            os.makedirs(self.iprefDirectory)

        self.appleAPIId = self.pluginPrefs.get('appleAPIid', '')

        # if self.appleAPIId != '':
        #
        #     self.logger.debug(u"self.appleAPIID is not empty - logging in to self.appleAPI now.")
        #     username = self.pluginPrefs.get('appleId')
        #     password = self.pluginPrefs.get('applePwd')
        #     self.appleAPI = self.iAuthorise(username, password)
        #
        #     if self.appleAPI[0] == 1:
        #         self.logger.debug(u"Login to icloud Failed.")


    def validateDeviceConfigUi(self, valuesDict, typeID, devId):
        """ Validate select device config menu settings. """

        # =============================================================
        # Device configuration validation Added DaveL17 17/12/19
        errorDict = indigo.Dict()
        self.logger.debug(u"validateDeviceConfigUi() method called.")
        return True, valuesDict, errorDict

    def validatePrefsConfigUi(self, valuesDict):
        """ docstring placeholder """
        self.logger.debug(u"validatePrefsConfigUi() method called.")
        accountOK = False
        errorDict = indigo.Dict()

        if 'appleId' in valuesDict:
            iFail = False
            if len(valuesDict['appleId']) == 0:
                # Blank username!
                iFail = True
                errorDict["appleId"] = "No username entered"
                errorDict[
                    "showAlertText"] = "You must obtain a valid Apple Account Username before installing this plugin"

            elif valuesDict['appleId'].find('@') == -1:
                # Not an email address as no @ symbol
                iFail = True
                errorDict["appleId"] = "Invalid email address as user name"
                errorDict["showAlertText"] = "Username doesn't appear to be an email address"

            if iFail:
                return (False, valuesDict, errorDict)

        else:
            return False, valuesDict

        if 'applePwd' in valuesDict:
            iFail = False
            if len(valuesDict['applePwd']) == 0:
                # Blank password!
                iFail = True
                errorDict["applePwd"] = "No password entered"
                errorDict["showAlertText"] = "You must enter a valid Apple Account password"

            if iFail:
                self.logger.info("applePwd failed")
                return (False, valuesDict, errorDict)

        if 'applePwd' in valuesDict and 'appleId' in valuesDict and valuesDict['TwoFAenabled']==False:
            # Validate login
            iLogin = self.iAuthorise(valuesDict['appleId'], valuesDict['applePwd'])
            if not iLogin[0] == 0:
                # Failed login
                iFail = True
                errorDict["appleId"] = "Could not log in with that username/password combination"
                errorDict["showAlertText"] = "Login validation failed - check username & password or internet connection"
            else:
                # Get account details
                self.appleAPI = iLogin[1]
                    #self.logger.info(u'Login Details**********:')
                    #self.logger.info(str(api.friends.locations))
                # dev = indigo.devices[devId]
                accountOK = True
                valuesDict['appleAPIid'] = valuesDict['appleId']
                #return True, valuesDict

            if iFail:
                self.logger.info("Login to Apple Server Failed")
                return (False, valuesDict, errorDict)

        self.wazeRegion = valuesDict.get('wazeRegion')
        self.wazeUnits = valuesDict.get('wazeUnits')

        return True, valuesDict


    def getTheData(self):
        """ The getTheData() method is used to retrieve target data files. """

        self.logger.debug(u"gettheData() method called.  Not in use.  Refresh instead")
        return

    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """
        self.logger.debug(u"refreshDataAction() method called.")
        self.refreshData()
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin devices.
        """

        self.logger.debug(u"refreshData() method called.")
        try:
            username = self.pluginPrefs.get('appleId', '')
            password = self.pluginPrefs.get('applePwd', '')
            appleAPIId = self.pluginPrefs.get('appleAPIid', '')
            Twofaenabled = self.pluginPrefs.get('TwoFAenabled', False)

            if appleAPIId == '':
                self.logger.info(u"{0:=^130}".format(""))
                self.logger.info(u"Plugin Config is not complete.")
                self.logger.info(u"Please go to Plugin Config Page and re-Login")
                self.logger.info(u"& enter 2FA as required")
                self.logger.info(u"{0:=^130}".format(""))
                return

           # if 2faenabled and self.2faverifed:

            iLogin = self.iAuthorise(username, password)

            if iLogin[0] == 1:
                self.logger.debug(u"Login to icloud Failed.")
                self.appleAPI = None
                return
            if iLogin[0] == 2:
                self.logger.debug(u"2FA Work flow needed. ")
                return
            if iLogin[0] == None:
                self.logger.debug("Error:")
                self.appleAPI = None
                return

            self.appleAPI = iLogin[1]

            follower = self.appleAPI.friends.locations
            friendsdata = iLogin[1].friends.data

            if self.debugicloud:
                self.logger.debug(str('Follower is Type: '+ str(type(follower))))
            if self.debugicloud:
                self.logger.debug(str('More debugging: Follower: '+str(follower)))
            if len(follower) == 0:
                self.logger.info(u'No Followers Found for this Account.  Have you any friends?')
                if self.debugicloud:
                    self.logger.debug(u'Full Dump of self.appleAPI data follows:')
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(str(friendsdata))
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u'Please PM developer this log.')
                    self.logger.debug(u"{0:=^130}".format(""))
                return

            if follower is None:
                self.logger.info(u'No Followers Found for this Account.  Have you any (enabled) friends?')
                if self.debugicloud:
                    self.logger.debug(u'Full Dump of self.appleAPI data follows:')
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(str(iLogin[1].friends.data))
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u'Please PM developer this log.')
                    self.logger.debug(u"{0:=^130}".format(""))
                return

            for dev in indigo.devices.iter("self.FindFriendsFriend"):
                # Check AppleID of Device
                if dev.enabled:
                    targetFriend = dev.pluginProps['targetFriend']
                    if self.debugicloud:
                        self.logger.debug(u'targetFriend of Device equals:' + str(targetFriend))
                    for follow in follower:
                        if self.debugicloud:
                            self.logger.debug (str(follow['id']))
                        if follow['id'] == targetFriend:
                            if self.debugicloud:
                                self.logger.debug(u'Found Target Friend in Data:  Updating Device:' + str(dev.name))
                                self.logger.debug(str(follow))
                            # Update device with data from iFindFriends service
                            self.refreshDataForDev(dev, follow)

            for dev in indigo.devices.iter("self.myDevice"):
                # Check AppleID of Device
                if dev.enabled:
                    targetFriend = dev.pluginProps['targetFriend']
                    if self.debugicloud:
                        self.logger.debug(u'targetDevice of Device equals:' + str(targetFriend))
                    devicetargets = self.appleAPI.devices
                    for devices in devicetargets:
                        #self.logger.error(str(devices))
                        #self.logger.error(devices['id'])
                        #self.logger.error(devices.status())
                        #self.logger.error(devices.location())
                        if str(targetFriend) == str(devices['id']):
                            self.refreshDataforMyDevice( dev, devices)

                    #elf.logger.error("**:"+str(targetdevice))

            return

        except PyiCloudAPIResponseException as e:
            self.logger.debug(u'Login Failed API Response Error.   ' + str(e) + str(e.__dict__))
            if e.code in [450,421,500]:
                self.logger.info("Error Code 450/421/500 Given: Re-authentication seems to be required.  Reauthenicating now.")
                self.appleAPI.authenticate(True)
                try:
                    self.logger.debug(u"Testing ********************************************")
                    self.logger.debug( str(self.appleAPI.devices[0] ))
                    self.logger.debug(u"********************************************")
                    self.sleep(5)
                    self.refreshData()

                except PyiCloudAPIResponseException:
                    self.logger.debug("Could not re-authenticate at all... Sorry.")
                    self.appleAPI = None
                    self.allDevicesOffline()
                    return 1, 'NI'
            self.logger.debug(e)
            return

        except PyiCloudFailedLoginException:
            self.logger.debug(u'Login failed - Check username/password - has it changed recently?. ')
            return

        except PyiCloud2SARequiredException:
            self.logger.info(u"{0:=^130}".format(""))
            self.logger.info(u'Login failed.  Account requires 2nd factor, verification code setup.  Please see Plugin config window, enter and submit verification code')
            self.logger.info(u"{0:=^130}".format(""))
            self.appleAPI = None
            self.requires2FA = True
            self.triggerCheck2fa()
            return

        except Exception as e:
            self.logger.info(u"{0:=^130}".format(""))
            self.logger.info(u'Error within get Data.  ?Network connection or issue:  Error Given: '+str(e))
            self.logger.info(u"{0:=^130}".format(""))
            self.logger.exception(u"Caught Exception")
          #  self.logger.info(u'Have you also logged on and setup new account on an Ios/iphone/ipad device?')
          #  self.logger.info(u'You need to run and enable iOS FindmyFriends Application, you should see visible friends')
         #   self.logger.info(u'This needs to be done, for FindmyFriends to work.  You cannot just create account.')
            self.logger.info(u"{0:=^130}".format(""))
            return



    def updateGeofencetime(self):
        try:

            self.logger.debug('update GeoFences time called')
            for geoDevices in indigo.devices.iter('self.FindFriendsGeofence'):
                if geoDevices.enabled:
                    #localProps = geoDevices.pluginProps
                    lastArrivaltimestamp = float(geoDevices.states['lastArrivaltimestamp'])
                    lastDeptimestamp = float(geoDevices.states['lastDeptimestamp'])
                    if lastArrivaltimestamp > 0:
                        #self.logger.info(str(lastArrivaltimestamp))
                        timesincearrival = int(t.time() - float(lastArrivaltimestamp)) / 60  # time in seconds /60
                        #self.logger.info(str(timesincearrival))
                        geoDevices.updateStateOnServer('minutessincelastArrival', value=timesincearrival)
                    if lastDeptimestamp > 0:
                        timesincedep = int(t.time() - float(lastDeptimestamp)) / 60
                        geoDevices.updateStateOnServer('minutessincelastDep', value=timesincedep)

        except Exception as e:
            self.logger.info(u'Error with updateGeoFence Time:' + str(e))
            pass

    def checkGeofence(self):
        try:

            self.logger.debug('Check GeoFences Called..')


            # need to start with GeofFence and then go through all devices
            # iDevName = dev.states['friendName']
            # Check GeoFences after devices
            for geoDevices in indigo.devices.iter('self.FindFriendsGeofence'):
                if geoDevices.enabled:
                    listFriends = []
                    igeoFriendsRange = 0
                    localProps = geoDevices.pluginProps
                    if not 'geoName' in localProps:
                        continue
                    igeoName = localProps['geoName']
                    igeoLong = float(localProps['geoLongitude'])
                    igeoLat = float(localProps['geoLatitude'])
                    igeoRangeDistance = int(localProps['geoRange'])
                    # old Friends in Range - act on changes.
                    igeoFriendsRangeOld = int(geoDevices.states['friendsInRange'])
                    iGeolistFriends = []
                    if geoDevices.states['listFriends'] != '':
                        iGeolistFriends = geoDevices.states['listFriends'].split(',')
                    self.logger.debug(u'Old GeoDevice Friends Equals:')
                    self.logger.debug(str(iGeolistFriends))

                    for dev in indigo.devices.iter("self.FindFriendsFriend"):
                        #add online check here
                        if dev.enabled and dev.states['deviceIsOnline'] == True:
                            self.logger.debug('Geo Details on check:' + str(igeoName) + ' For Friend:' + str(dev.name))
                            iDevLatitude = float(dev.states['latitude'])
                            iDevLongitude = float(dev.states['longitude'])
                            iDevUniqueName = dev.pluginProps['friendName']
                            iDevAccuracy = float(dev.states['horizontalAccuracy'])


                            #self.logger.error(str(iDevUniqueName))
                            # Now check the distance for each device
                            # Calculate the distance

                            self.logger.debug('Point 1' + ' ' + str(igeoLat) + ',' + str(igeoLong) + ' Point 2 ' + str(iDevLatitude) + ',' + str(iDevLongitude))
                            iSeparation = self.iDistance(igeoLat, igeoLong, iDevLatitude, iDevLongitude)

#######################################################################################################################################
# Tested extensively comparing Google Distance Calculation to World Sphere Calculation
# Turns out Google uses Road distance and not as 'crow flies' so not that useful
# Leave this code here for future reference, in case what to revisit

                          #  self.newlogger.debug('Point 1' + ' ' + str(igeoLat) + ',' + str(igeoLong) + ' Point 2 ' + str(
                          #      iDevLatitude) + ',' + str(iDevLongitude))
                          #  self.newlogger.debug(u'Calculated Separation: ='+str(iSeparation[1]))
                          # Compare with Google Call - Google uses driving distance
                          #  origin = igeoLat, igeoLong
                          #  destination = iDevLatitude, iDevLongitude
                          #  GoogleDistanceHome = self.distanceCalculation(origin, destination, self.googleAPI, 'driving', "metric")
                          #  RealDistanceHome = int(float(GoogleDistanceHome[3]))
                          #  self.newlogger.debug(u'Google Distance Apart:='+str(RealDistanceHome))
                          #  self.logger.debug(u'Google Distance:'+str(RealDistanceHome))
########################################################################################################################################

                            self.logger.debug(u'Calculated Distance:'+str(iSeparation[1]))
                            if not iSeparation[0]:
                                self.logger.debug(u'Problem with iSeparation.  Continue.')
                        # Problem with the distance so ignore and move on
                                continue
                            iSeparationABS = abs(iSeparation[1])
                    # if distance between to points smaller than range of GeoFence then is 'InRange' or within Geofence
                    # now need to count numbers.
                    ##
                    ##  Deal with horizontal accuracy
                    ##
                    ## log it all
                            ##
                            self.logger.debug(u'---------------- Horizontal Accuracy :'+str(iDevUniqueName)+' & Geo:'+str(igeoName))
                            self.logger.debug(u'---------------- Distance apart:'+str(iSeparationABS)+'    Accuracy:'+str(iDevAccuracy)+'  Geo Range:'+str(igeoRangeDistance)+'-----')

# below is not correct and could be plus or minus this distance

                           # DistanceApartAccuracy = abs(iSeparationABS - iDevAccuracy )
                            RatioAccuracyGeofencerange = float(iDevAccuracy/igeoRangeDistance)

                            DistanceAccurate = float(iSeparationABS-iDevAccuracy)
                            if DistanceAccurate <=0:
                                DistanceAccurate =0
                            if self.debuggeofence:
                                self.newlogger.debug(u'Geofence:'+str(igeoName)+ ' '*(30-len(igeoName))+u'| Device:'+str(iDevUniqueName)+ ' '*(23-len(iDevUniqueName))+u'| iSeparationABS:'+str(iSeparationABS)+ ' '*(18-len(str(iSeparationABS)))+u'| iDevAccuracy:'+str(iDevAccuracy) + ' '*(15-len(str(iDevAccuracy)))+ u'| DistanceAccurate Result equals:'+str(DistanceAccurate))

# need to not update if % of GeoFence versus Accuracy e.g if 100 m Geofence and accuracy 1000m don't add
# but if 1000m Geofence and accuracy +/- 1000m add.  Trial ratio of 2 as cut-off.
# Accuracy/GeoFence Range

                    #       self.logger.debug(u'---------------  Distance Apart Calculation:'+str(DistanceApartAccuracy))
                    ## only add or remove if accurate - need to check if there already first to enable this
                    ##

                            self.logger.debug(u'---------------- Checking :' + str(iDevUniqueName) + ' whether appears to be within Lists of Friends (:' + geoDevices.states['listFriends'])
                            self.logger.debug(u'---------------- Accuracy versus Geofence Range equals:'+str(iDevAccuracy/igeoRangeDistance))

                            if float(iDevAccuracy/igeoRangeDistance) <= 2:
                                # if friend in geofence and distance still within.  Does not alter with accuracy ?-
                                #self.logger.debug(u'------------------ iDevAccuracy versus GeoRange Less than 2:  Current='+str(RatioAccuracyGeofencerange))
                                #self.newlogger.debug(u'------------------ iDevAccuracy versus GeoRange Less than 2:  Current=' + str(  RatioAccuracyGeofencerange))
                                if iDevUniqueName in geoDevices.states['listFriends'] and DistanceAccurate <= igeoRangeDistance:  #if already present ignore accuracy data
                                    self.logger.debug(u'---------------- Located via accurate WITHIN Geofence:' + str(iDevUniqueName) + ' appears to be within Friends.')
                                    iDevGeoInRange = 'true'
                                    igeoFriendsRange = igeoFriendsRange + 1
                                    listFriends.append(iDevUniqueName)
                                # if not in friend list and accurate location - yes add to geofence
                                elif iDevUniqueName not in geoDevices.states['listFriends'] and DistanceAccurate <= igeoRangeDistance:
                                    self.logger.debug(u'---------------- Located within Accurate Geofence:' + str(iDevUniqueName) + '& appears to be NOT within Friends List: Add to Geofence')
                                    iDevGeoInRange = 'true'
                                    self.logger.debug(u'*****************'+str(iDevUniqueName)+u' Added to GeoFence:'+str(igeoName)+' Ratio :'+str(RatioAccuracyGeofencerange)+u'  Distance:'+str(iSeparationABS)+' HorizontalAccuracy:'+str(iDevAccuracy)+ u'     DistanceAccurate Result equals:'+str(DistanceAccurate))
                                    if self.debuggeofence:
                                        self.newlogger.info(u"{0:=^150}".format(""))
                                        self.newlogger.debug(str(iDevUniqueName)+u' - ADDED - GeoFence:'+str(igeoName)+ ' '*(25-len(igeoName))+' Ratio :'+str(RatioAccuracyGeofencerange)+ ' '*(18-len(str(RatioAccuracyGeofencerange)))+u'  Distance:'+str(iSeparationABS)+ ' '*(18-len(str(iSeparationABS)))+' HorizontalAccuracy:'+str(iDevAccuracy)+ ' '*(6-len(str(iDevAccuracy)))+ u' DistanceAccurate Result equals:'+str(DistanceAccurate))
                                        self.newlogger.info(u"{0:=^150}".format(""))
                                    igeoFriendsRange = igeoFriendsRange + 1
                                    listFriends.append(iDevUniqueName)
                                #if in geofence use accurate. Don't remove unless acurrate.
                                elif iDevUniqueName in geoDevices.states['listFriends'] and DistanceAccurate > igeoRangeDistance:
                                    # if in geofence friends list and clearly, accurately left - make as gone.
                                    self.logger.debug(u'---------------- Outside Accurate Range :' + str(iDevUniqueName) + ' in Friends List. Dont add to Geofence')
                                    self.logger.debug(
                                        str(iDevUniqueName) + u' - REMOVED - GeoFence:' + str(igeoName) + ' ' * (
                                                    25 - len(igeoName)) + ' Ratio :' + str(
                                            RatioAccuracyGeofencerange) + ' ' * (18 - len(
                                            str(RatioAccuracyGeofencerange))) + u'  Distance:' + str(
                                            iSeparationABS) + ' ' * (
                                                    18 - len(str(iSeparationABS))) + ' HorizontalAccuracy:' + str(
                                            iDevAccuracy) + ' ' * (6 - len(
                                            str(iDevAccuracy))) + u' DistanceAccurate Result equals:' + str(
                                            DistanceAccurate))

                                    self.logger.debug(u'*****************'+str(iDevUniqueName)+u' Removed GeoFence:'+str(igeoName)+'  Ratio:'+str(RatioAccuracyGeofencerange)+u'  Distance:'+str(iSeparationABS)+' HorizontalAccuracy:'+str(iDevAccuracy)+ u'     DistanceAccurate Result equals:'+str(DistanceAccurate))
                                    if self.debuggeofence:
                                        self.newlogger.info(u"{0:=^160}".format(""))
                                        self.newlogger.debug(str(iDevUniqueName)+u' REMOVED: GeoFence:'+str(igeoName)+ ' '*(25-len(igeoName))+' Ratio :'+str(RatioAccuracyGeofencerange)+ ' '*(18-len(str(RatioAccuracyGeofencerange)))+u'  Distance:'+str(iSeparationABS)+ ' '*(18-len(str(iSeparationABS)))+' HorizontalAccuracy:'+str(iDevAccuracy)+ ' '*(6-len(str(iDevAccuracy)))+ u' DistanceAccurate Result equals:'+str(DistanceAccurate))
                                        self.newlogger.info(u"{0:=^160}".format(""))
                                    iDevGeoInRange = 'false'
                                #if not in geofence don't make as absence without accurate data
                                elif iDevUniqueName not in geoDevices.states['listFriends'] and DistanceAccurate > igeoRangeDistance:
                                    # if not in friends list - can be gone, make sure not added
                                    self.logger.debug(u'---------------- Outside Accurate Range :' + str(iDevUniqueName) + ' and not in Friends List. Dont add to Geofence.')
                                    iDevGeoInRange = 'false'
                            elif float(iDevAccuracy / igeoRangeDistance) > 2:
                                self.logger.debug(u'------------------ Accuracy Poor:  Checking whether already within Geofence & Distance.  Distance calculated:'+str(iSeparationABS)+u' GeoRangDistance:'+str(igeoRangeDistance)+ u'     DistanceAccurate Result equals:'+str(DistanceAccurate))
                                #self.newlogger.debug(u'------------------ Accuracy Poor:  Checking whether already within Geofence & Distance.  Distance calculated:'+str(iSeparationABS)+u' GeoRangDistance:'+str(igeoRangeDistance)+ u'     DistanceAccurate Result equals:'+str(DistanceAccurate))

                                # may be better to remove distance check here altogether and only remove if good accuracy
                                # but depends how far away the device is
                                # this may be the space to look at more complication accuracy versus seperation type calculation
                                # will run and gather more data first
                                # change here - not accurate do not remove rom Geofence
                                if iDevUniqueName in geoDevices.states['listFriends']: #//remoce this check and DistanceAccurate <= igeoRangeDistance:  #if already present ignore accuracy data
                                    self.logger.debug(u'---------------- Accuracy Poor: ' + str(iDevUniqueName) + ' & Is WITHIN Geofence:' + str(igeoName) + ', poor accuracy so do not remove.  Distance:'+str(iSeparationABS)+ u'    DistanceAccurate --Used-- Result equals:'+str(DistanceAccurate))
                                    if self.debuggeofence:
                                        self.newlogger.info(u"{0:=^160}".format(""))
                                        self.newlogger.debug(str(iDevUniqueName)+u' POOR ACCURACY In Geofence: GeoFence:'+str(igeoName)+ ' '*(25-len(igeoName))+' Ratio :'+str(RatioAccuracyGeofencerange)+ ' '*(18-len(str(RatioAccuracyGeofencerange)))+u'  Distance:'+str(iSeparationABS)+ ' '*(18-len(str(iSeparationABS)))+' HorizontalAccuracy:'+str(iDevAccuracy)+ ' '*(6-len(str(iDevAccuracy)))+ u' DistanceAccurate Result equals:'+str(DistanceAccurate))
                                        self.newlogger.info(u"{0:=^160}".format(""))
                                    iDevGeoInRange = 'true'
                                    igeoFriendsRange = igeoFriendsRange + 1
                                    listFriends.append(iDevUniqueName)
                        elif dev.enabled and dev.states['deviceIsOnline']==False:
                            # add check here for offline device
                            # if server down for 1/2 hour for example don't remove from geofence or add to geofence why down.
                            iDevUniqueName = dev.pluginProps['friendName']
                            if iDevUniqueName in geoDevices.states['listFriends']:
                                self.logger.debug(u'-*-*-*-*-*-*-*-*-*-*-*-* Offline Device:'+str(iDevUniqueName)+u' is OFFLINE and within Geofence:'+str(igeoName) +u'  .Dont remove why offline')
                                if self.debuggeofence:
                                    self.newlogger.info(u"{0:=^160}".format(""))
                                    self.newlogger.debug(u'Offline Device:' + str(iDevUniqueName) + u' is OFFLINE and within Geofence:' + str(igeoName) + u'  .Dont remove why offline')
                                    self.newlogger.info(u"{0:=^160}".format(""))
                                iDevGeoInRange = 'true'
                                igeoFriendsRange = igeoFriendsRange + 1
                                listFriends.append(iDevUniqueName)

                        #End of Device Ieration
                    #Now back to GeoFence iteration

                    update_time = t.strftime(self.datetimeFormat)
                    if igeoFriendsRange != igeoFriendsRangeOld:
                                # Has been change to the igeoFriends Number
                                # Should Update now
                        geoDevices.updateStateOnServer('friendsInRange', value=int(igeoFriendsRange))
                    if igeoFriendsRangeOld > igeoFriendsRange:
                                    #More friends in range before, someone must have left
                                    # Update leave time
                        geoDevices.updateStateOnServer('lastDeptime', value=update_time)
                        geoDevices.updateStateOnServer('lastDeptimestamp', value=t.time())
                    elif igeoFriendsRangeOld < igeoFriendsRange:
                                    #Less People previously, someone must have arrived
                                    # update arrival time
                        geoDevices.updateStateOnServer('lastArrivaltime', value=update_time)
                        geoDevices.updateStateOnServer('lastArrivaltimestamp', value=t.time())
                            # Change Sensor Icon
                    if igeoFriendsRange==0:
                        geoDevices.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                        geoDevices.updateStateOnServer("occupied", value=False)
                    if igeoFriendsRange >0:
                        geoDevices.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                        geoDevices.updateStateOnServer("occupied", value=True)
                    geoDevices.updateStateOnServer('listFriends', value=str(",".join(listFriends )))
                    # go through old list of friends and compare to new list
                    try:
                        self.logger.debug(u'Old Friends: iGeolistFriends: '+str(iGeolistFriends))
                        self.logger.debug(u'len of iGeoListFriends:'+str(len(iGeolistFriends)))
                        if len(iGeolistFriends)>0:
                            for oldfriend in iGeolistFriends:
                                self.logger.debug(u'OldFriend List iteration: OldFriend:'+str(oldfriend))
                                if listFriends.count(oldfriend)==0:
                                    self.logger.debug(u'OldFriend no longer present; count=0; must have left')
                                    self.logger.debug(str(oldfriend)+str(' Has Left GeoFence:'+igeoName))
                                    self.triggerCheck(geoDevices, oldfriend, 'EXIT')
                                #elif listFriends.count(oldfriend) >0:  #probably not needed below
                                #    self.logger.debug(u'Oldfriend and current friend still present.  Do Nothing.')
                                #    self.logger.debug(str(oldfriend) + str(' Still within GeoFence:' + igeoName))
                        self.logger.debug(u'New Friends: listFriends: ' + str(listFriends))
                        self.logger.debug(u'len of listFriends:' + str(len(listFriends)))
                        if len(listFriends)>0:
                            for newfriend in listFriends:
                                self.logger.debug(u'newFriend List iteration:  NewFriend:'+str(newfriend))
                                if iGeolistFriends.count(newfriend)==0:
                                    self.logger.debug(u'newfriend count =0, means not current friend not present in old list.  Must have arrived.')
                                    self.logger.debug(str(newfriend) + str(' Has Arrived with GeoFence:' + igeoName))
                                    self.triggerCheck( geoDevices, newfriend, 'ENTER')
                    except:
                        self.logger.exception(u'Error Comparing old and new friends within GeoFence')
                        pass

                    try:
                        lastArrivaltimestamp = float(geoDevices.states['lastArrivaltimestamp'])
                        lastDeptimestamp = float(geoDevices.states['lastDeptimestamp'])
                        if lastArrivaltimestamp > 0:
                            #self.logger.info(str(lastArrivaltimestamp))
                            timesincearrival = int(t.time()-float(lastArrivaltimestamp))/60  #time in seconds /60
                            #self.logger.info(str(timesincearrival))
                            geoDevices.updateStateOnServer('minutessincelastArrival', value=timesincearrival)
                        if lastDeptimestamp >0:
                            timesincedep = int(t.time()-float(lastDeptimestamp))/60
                            geoDevices.updateStateOnServer('minutessincelastDep', value=timesincedep)
                    except Exception as e:
                        self.logger.info(u'Error with Departure/Arrival Time Calculation:'+str(e))
                        pass

                    geoDevices.updateStateOnServer('deviceIsOnline', value=True, uiValue='Online')


        except Exception as e:
            self.logger.info(u'Error within Check GeoFences: '+str(e))
            geoDevices.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
            return

    def getLatLong(self, valuesDict=None, typeId="", dev=0):
        ################################################
        # Opens a web Browser so user can find a latitude and longitude for an address
        # Uses www.latlong.com
        try:
            iurl="http://www.latlong.net"
            self.browserOpen(iurl)
        except:
            self.logger.error(u'Default web browser did not open - check Mac set up')
            self.logger.error(u'or issues contacting the www.latlong.net site.  Is internet working?')
        return

    def refreshDataforMyDevice(self,dev, appleDevice):
        self.logger.debug(u"refreshDataforMyDevice() method called.")
        try:
            if self.debugicloud:
                self.logger.debug(str('Now updating Data for : ' + str(dev.name) + ' with data received: '))

            # self.logger.error(str(devices))
            # self.logger.error(devices['id'])
            # self.logger.error(devices.status())
            # self.logger.error(devices.location())

            locationdata = appleDevice.location()
            devicestatus = appleDevice.status(additional=["deviceModel","batteryStatus"])
            deviceid = appleDevice['id']

            if appleDevice is None:
                self.logger.debug(u'No data received for device:' + str(
                    dev.name) + ' . Most likely device is offline/airplane mode or has disabled sharing location')
                if dev.states['deviceIsOnline']:
                    self.logger.info(u'myOwnDevice Device:' + str(
                        dev.name) + ' has become Offline.  Most likely offline/airplane mode or disabled sharing')
                    dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                return

            if locationdata is None:
                self.logger.debug(u'No data received for device:' + str(
                    dev.name) + ' . Most likely device is offline/airplane mode or has disabled sharing location')
                if dev.states['deviceIsOnline']:
                    self.logger.info(u'Friend Device:' + str(
                        dev.name) + ' has become Offline.  Most likely offline/airplane mode or disabled sharing')
                    dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                return

            if locationdata == 'None':
                self.logger.debug(u'No data received for device:' + str(
                    dev.name) + ' . Most likely device is offline/airplane mode or has disabled sharing location')
                if dev.states['deviceIsOnline']:
                    self.logger.info(u'Friend Device:' + str( dev.name) + ' has become Offline.  Most likely offline/airplane mode or disabled sharing')
                    dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                return

            latitude = locationdata['latitude']
            longitude = locationdata['longitude']

            if dev.states['latitude'] != 'unknown':
                iDevLatitude = float(dev.states['latitude'])
                iDevLongitude = float(dev.states['longitude'])
                # Check to see whether moved and by how much since last check
                Distancetravelled = self.iDistance(iDevLatitude, iDevLongitude, float(latitude),
                                                   float(longitude))
            else:
                Distancetravelled = False, 0

            batteryLevel = 0
            try:
                batteryLevel =  round(float(devicestatus['batteryLevel'])*100,3)
                self.logger.debug(u"Converted Battery to:"+str(batteryLevel))
            except:
                self.logger.debug("Error in Battery Level conversion")
            devSummary = "Offline"
            try:
                devSummary = str("Bat "+str(int(batteryLevel))+"% and "+str(devicestatus['batteryStatus']))
            except:
                devSummary = "Unknown"
                self.logger.debug("Error in devSummary")

            stateList = [
                {'key': 'id', 'value': deviceid},
                {'key': 'deviceName', 'value': devicestatus['deviceDisplayName']},
                {'key': 'deviceModel', 'value': devicestatus['deviceModel']},
                {'key': 'deviceStatus', 'value': devicestatus['deviceStatus']},
                {'key': 'status', 'value': devicestatus['deviceStatus']},
                {'key': 'batteryStatus', 'value': devicestatus['batteryStatus']},
                {'key': 'batteryCharge', 'value': batteryLevel},
                {'key': 'devSummary', 'value': devSummary},
                {'key': 'locationTimestamp', 'value': locationdata['timeStamp']},
                {'key': 'timestamp', 'value': locationdata['timeStamp']},
                {'key': 'altitude', 'value': locationdata['altitude']},
                {'key': 'longitude', 'value': longitude},
                {'key': 'horizontalAccuracy', 'value': locationdata['horizontalAccuracy']},
                {'key': 'latitude', 'value': latitude},
                {'key': 'distanceSinceCheck', 'value': str(Distancetravelled[1])},
            ]

            self.logger.debug(str(stateList))

            dev.updateStatesOnServer(stateList)
            # Change to strftime user selectable date for DeviceLastUpdate field
            # Is Plugin config selectable

            update_time = t.strftime(self.datetimeFormat)
            dev.updateStateOnServer('deviceLastUpdated', value=str(update_time))
            dev.updateStateOnServer('deviceTimestamp', value=t.time())
            dev.updateStateOnServer('deviceIsOnline', value=True)
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

            if Distancetravelled[0] == True and int(Distancetravelled[1] > 100):
                self.logger.debug(u'Device has travelled - setting mapUpdateNeeded to true')
                dev.updateStateOnServer('mapUpdateNeeded', value=True)

            self.godoMapping(str(latitude), str(longitude), dev)

        except Exception as e:
            self.logger.debug(str('Exception in refreshDataformyDevice: ' + str(e)))
            self.logger.debug('Exception:')
            self.logger.exception(str('Possibility missing some data from icloud:  Is your account setup with FindFriends enabled on iOS/Mobile device?'))
            dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            return


    def refreshDataForDev(self, dev, follow):
        """ Refreshes device data. """
        self.logger.debug(u"refreshDataForDev() method called.")
        try:
            if self.debugicloud:
                self.logger.debug(
                str('Now updating Data for : ' + str(dev.name) + ' with data received: ' + str(follow)))
#
#
# Manage Labels provided by icloud data set
#
#
            #Check for no data received and handle avoiding exception
            #unless starting up (60 seconds only)
            #if self.startingUp==False or self.startingUp==True:
            if follow is None:
                self.logger.debug(u'No data received for device:' + str( dev.name) + ' . Most likely device is offline/airplane mode or has disabled sharing location')
                if dev.states['deviceIsOnline']:
                    self.logger.info(u'Friend Device:' + str(dev.name) + ' has become Offline.  Most likely offline/airplane mode or disabled sharing')
                    dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                return
            if 'location' not in follow:
                self.logger.debug(u'No data received for device:' + str(
                    dev.name) + ' . Most likely device is offline/airplane mode or has disabled sharing location')
                if dev.states['deviceIsOnline']:
                    self.logger.info(u'Friend Device:' + str(
                        dev.name) + ' has become Offline.  Most likely offline/airplane mode or disabled sharing')
                    dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                return
            if follow['location'] is None or follow['location'] == 'None':
                self.logger.debug(u'No data received for device:'+str(dev.name)+' . Most likely device is offline/airplane mode or has disabled sharing location')
                if dev.states['deviceIsOnline']:
                    self.logger.info(u'Friend Device:'+str(dev.name)+' has become Offline.  Most likely offline/airplane mode or disabled sharing')
                    dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                return


            UseLabelforState = False
            # Deal with Label Dict either Dict or None
            labels=''
            if follow is not None:
                if 'location' in follow:
                    if follow['location'] is not None:
                        if 'labels' in follow['location']:
                            if follow['location']['labels'] is not None:
                                labels = follow['location']['labels']
            #another none check - shouldnt be needed
            if len(labels) > 0:
                label = labels[0]
            else:
                label = labels

            if self.debugicloud:
                self.logger.debug(str('Label:' + str(label) + ' and type is ' + str(type(label))))

            labeltouse = 'nil'
            if isinstance(label, dict):
                if 'label' in label and label['label'] is not None:
                    labeltouse = label['label']
                    UseLabelforState = True
                    nonletter = '$_<>!'
                    labeltouse = labeltouse.strip(nonletter)
                    labeltouse = labeltouse.capitalize()
            elif isinstance(label, list):
                labeltouse = ','.join(follow['location']['labels'])
            elif label == None:
                labeltouse = 'nil'
#

            address =""
            if follow is not None:
                if 'location' in follow:
                    if follow['location'] is not None:
                        if 'address' in follow['location'] and follow['location']['address'] is not None:
                            if 'formattedAddressLines' in follow['location']['address'] and follow['location']['address']['formattedAddressLines'] is not None:
                                address = ','.join(follow['location']['address']['formattedAddressLines'])
                            if 'streetAddress' in follow['location']['address'] and follow['location']['address']['streetAddress'] is not None:
                                address = follow['location']['address']['streetAddress']
                            if 'locality' in follow['location']['address'] and follow['location']['address']['locality'] is not None:
                                address = address + ' '+ follow['location']['address']['locality']

            if dev.states['latitude'] != 'unknown':
                iDevLatitude = float(dev.states['latitude'])
                iDevLongitude = float(dev.states['longitude'])
            # Check to see whether moved and by how much since last check
                Distancetravelled = self.iDistance( iDevLatitude, iDevLongitude, float(follow['location']['latitude']), float(follow['location']['longitude']))
            else:
                Distancetravelled = False,0

            stateList = [
                {'key': 'id', 'value': follow['id']},
                {'key': 'status', 'value': follow['status']},
                {'key': 'locationStatus', 'value': follow['locationStatus']},
                {'key': 'batteryStatus', 'value': follow['location']['batteryStatus']},
                {'key': 'locationTimestamp', 'value': follow['location']['locationTimestamp']},
                {'key': 'timestamp', 'value': follow['location']['timestamp']},
                {'key': 'altitude', 'value': follow['location']['altitude']},
                {'key': 'labels', 'value': labeltouse},
                {'key': 'longitude', 'value': follow['location']['longitude']},
                {'key': 'horizontalAccuracy', 'value': follow['location']['horizontalAccuracy']},
                {'key': 'address', 'value': address},
                {'key': 'latitude', 'value': follow['location']['latitude']},
                {'key': 'distanceSinceCheck', 'value': str(Distancetravelled[1])},
            ]

            self.logger.debug(str(stateList))

            dev.updateStatesOnServer(stateList)
# Change to strftime user selectable date for DeviceLastUpdate field
# Is Plugin config selectable

            update_time = t.strftime(self.datetimeFormat)
            dev.updateStateOnServer('deviceLastUpdated', value=str(update_time))
            dev.updateStateOnServer('deviceTimestamp', value=t.time())
            if UseLabelforState:
                dev.updateStateOnServer('deviceIsOnline', value=True, uiValue=labeltouse)
            else:
                dev.updateStateOnServer('deviceIsOnline', value=True, uiValue=dev.states['address'])
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

            #
            if Distancetravelled[0]==True and int(Distancetravelled[1]>100):
                self.logger.debug(u'Device has travelled - setting mapUpdateNeeded to true')
                dev.updateStateOnServer('mapUpdateNeeded',value=True)

            self.godoMapping(str(follow['location']['latitude']),str(follow['location']['longitude']),dev)
            return

        except Exception as e:
            self.logger.debug(str('Exception in refreshDataforDev: ' + str(e)))
            self.logger.debug('Exception:')
            self.logger.exception(str('Possibility missing some data from icloud:  Is your account setup with FindFriends enabled on iOS/Mobile device?'))
            dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            return

    def requestSaveUrl(self, url, file):
        try:
            self.logger.debug("Saving url"+url+" as file:"+file)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

            r = requests.get(url, headers=headers, stream=True, timeout=10)
            with open(file, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        except:
            if self.debugmaps:
                self.logger.exception("Exception in saveURL Requests")
            self.logger.debug("Exception in save Map Requests")

    def godoMapping(self, latitude, longitude, dev):

        self.logger.debug(u"godoMapping() method called.")
        try:
            if not self.useMaps:
                if self.debugmaps:
                    self.logger.debug("UseMaps not enabled.  Returning.")
                return

            MAChome = os.path.expanduser("~") + "/"
            folderLocation = MAChome + "Documents/Indigo-iFindFriendMini/"

            filename = dev.name.replace(' ','_')+'_Map.jpg'
            file = folderLocation +filename
            #Generate single device URL

            if dev.states['mapUpdateNeeded']:
                self.logger.debug(u'update Map Happening as device moved..')
                drawUrl = self.urlGenerate(latitude ,longitude ,self.googleAPI, int(self.configHorizontalMap), int(self.configVerticalMap), int(self.configZoomMap), dev)
                if self.debugmaps:
                    self.logger.debug(u'drawURL 0=:'+str(drawUrl[0]))

                if self.debugmaps:
                    webbrowser.open_new(drawUrl[0])
                    #webbrowser.open_new(drawUrl[1])

                #fileMap = "curl --output '" + file + "' --url '" + drawUrl[0] + "'"
                #os.system(fileMap)

                self.requestSaveUrl(drawUrl[0],file)


                self.logger.debug('Saving Map...' + file)

                filename = 'All_device.jpg'
                file = folderLocation + filename
                #    Generate URL for All Maps - if using Google; not with openstreetmap
                if self.mapType=='google':
                    drawUrlall = self.urlAllGenerate(self.googleAPI,  int(self.configHorizontalMap), int(self.configVerticalMap), int(self.configZoomMap))
                    #fileMap = "curl --output '" + file + "' --url '" + drawUrlall + "'"
                    #os.system(fileMap)
                    self.requestSaveUrl(drawUrlall, file)
                    if self.debugmaps:
                        self.logger.debug('Saving Map...' + file)

                dev.updateStateOnServer('mapUpdateNeeded',value=False)

                dev.updateStateOnServer('googleMapUrl', value=str(drawUrl[1]) )
                self.logger.debug(u'Updating Variable:'+str(dev.name))

                variablename =''.join(dev.name.split())
                self.updateVar(variablename, str(drawUrl[1]))
                update_time = t.strftime(self.datetimeFormat)
                dev.updateStateOnServer('mapLastUpdated', value=str(update_time))

                if self.debugmaps and self.mapType=='google':
                    webbrowser.open_new(drawUrlall)
                    self.logger.debug(u'Mapping URL:')
                    self.logger.debug(str(drawUrlall))
                return
            else:
                self.logger.debug(u'No Mapping Needed.')
                return


        except Exception as e:
            self.logger.exception(u'Exception within godoMapping: '+str(e))


    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected
        device based on a plugin action call.
        """

        self.logger.debug(u"refreshDataForDevAction() method called.")
        return True


    def toggleDebugEnabled(self):
        """ Toggle debug on/off. """


        self.logger.debug(u"toggleDebugEnabled() method called.")

        if self.debugLevel == int(logging.INFO):
            self.debug = True
            self.debugLevel = int(logging.DEBUG)
            self.pluginPrefs['showDebugInfo'] = True
            self.pluginPrefs['showDebugLevel'] = int(logging.DEBUG)
            self.logger.info(u"Debugging on.")
            self.logger.debug(u"Debug level: {0}".format(self.debugLevel))
            self.logLevel = int(logging.DEBUG)
            self.logger.debug(u"New logLevel = " + str(self.logLevel))
            self.indigo_log_handler.setLevel(self.logLevel)

        else:
            self.debug = False
            self.debugLevel = int(logging.INFO)
            self.pluginPrefs['showDebugInfo'] = False
            self.pluginPrefs['showDebugLevel'] = int(logging.INFO)
            self.logger.info(u"Debugging off.  Debug level: {0}".format(self.debugLevel))
            self.logLevel = int(logging.INFO)
            self.logger.debug(u"New logLevel = " + str(self.logLevel))
            self.indigo_log_handler.setLevel(self.logLevel)

    def toggleDebugMax(self):
        """ Toggle debug on/off. """


        self.logger.debug(u"toggleDebugMax() method called.")

        self.debug = True
        self.debugLevel = int(logging.DEBUG)
        self.pluginPrefs['showDebugInfo'] = True
        self.pluginPrefs['showDebugLevel'] = int(logging.DEBUG)
        self.logger.info(u"Debugging on.")
        self.logger.debug(u"Debug level: {0}".format(self.debugLevel))
        self.logLevel = int(logging.DEBUG)
        self.logger.debug(u"New logLevel = " + str(self.logLevel))
        self.indigo_log_handler.setLevel(self.logLevel)

    def myFriendDevices(self, filter=0, valuesDict=None, typeId="", targetId=0):

        ################################################
        # Internal - Lists the Friends linked to an account
        try:

            self.logger.debug(str(u'myFriendDevices Called...'))
            # try:
            # Create an array where each entry is a list - the first item is
            # the value attribute and last is the display string that will be shown
            # Devices filtered on the chosen account

            #self.logger.info(str(valuesDict))
            iFriendArray = []
            username = self.pluginPrefs.get('appleId', '')
            password = self.pluginPrefs.get('applePwd', '')
            appleAPIId = self.pluginPrefs.get('appleAPIid', '')

            if appleAPIId == '':
                iWait = 0, "Set up Apple Account in Plugin Config"
                iFriendArray.append(iWait)
                return iFriendArray
                # go no futher unless have account details entered

            iLogin = self.iAuthorise(username, password)

            if iLogin[0] == 1:

                self.logger.debug(u"Login to icloud Failed.")
                iWait = 0, 'Login to icloud Failed'
                iFriendArray.append(iWait)
                return iFriendArray

            following = iLogin[1].friends.data['following']
            for fol in following:
                # self.logger.info(str(fol['id']))
                # self.logger.info(str(fol['invitationFromEmail']))
                iOption2 = fol['id'], fol['invitationAcceptedByEmail']
                #self.logger.info(str(iOption2))
                iFriendArray.append(iOption2)
            return iFriendArray

        except:
            self.logger.info(u'Error within myFriendsDevices')
            return []


    def myDevices(self, filter=0, valuesDict=None, typeId="", targetId=0):

        ################################################
        # Internal - Lists the Friends linked to an account
        try:

            self.logger.debug(str(u'myDevices Called...'))
            # try:
            # Create an array where each entry is a list - the first item is
            # the value attribute and last is the display string that will be shown
            # Devices filtered on the chosen account

            # self.logger.info(str(valuesDict))
            iArray = []
            username = self.pluginPrefs.get('appleId', '')
            password = self.pluginPrefs.get('applePwd', '')
            appleAPIId = self.pluginPrefs.get('appleAPIid', '')

            if appleAPIId == '':
                iWait = 0, "Set up Apple Account in Plugin Config"
                iArray.append(iWait)
                return iArray
                # go no futher unless have account details entered

            iLogin = self.iAuthorise(username, password)

            if iLogin[0] == 1:
                self.logger.debug(u"Login to icloud Failed.")
                iWait = 0, 'Login to icloud Failed'
                iArray.append(iWait)
                return iArray

            following = iLogin[1].devices
            #devicetargets = self.appleAPI.devices

            for fol in following:
                self.logger.debug(str(fol['id'])+" and "+str(fol['name']))

                iOption2 = fol['id'], fol['name']
                # self.logger.info(str(iOption2))
                iArray.append(iOption2)
            return iArray

        except:
            self.logger.exception(u'Error within myDevices')
            return []

    def allDevicesOffline(self):
        self.logger.debug("all Devices Offline")
        for dev in indigo.devices.iter("self"):
            # add check here make sure dev is Online before checking details of GeoFences
            if dev.enabled:
                dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
        return


    def iAuthorise(self, iUsername, iPassword):
        ################################################s
        # Logs in and authorises access to the Find my Phone API
        # Logs into the find my phone API and returns an error if it doesn't work correctly

        self.logger.debug('iAuthorise: Attempting login...')
        # Logs into the API as required
        try:
            if self.appleAPI == None:
                self.appleAPI = PyiCloudService(iUsername, iPassword, cookie_directory=self.iprefDirectory, session_directory=self.iprefDirectory+"/session", verify=True)
                self.logger.debug(u"PyiCloudService start or redo FULL self.appleAPI full login...")
                self.logger.debug(u'Login to account successful...')
                self.logger.debug(u"Account Requires 2FA:" + str(self.appleAPI.requires_2fa))

            if self.appleAPI:
                self.appleAPI.authenticate(force_refresh=False)
                self.logger.debug(u'Refresh Session appleAPI only.')

            self.requires2FA = self.appleAPI.requires_2fa
            if self.requires2FA:
                self.logger.info(u"{0:=^130}".format(""))
                self.logger.info(u"{0:=^130}".format(""))
                self.logger.info( u"Account requires a two step authentication:  Please see Plugin Config box to complete")
                self.logger.info(u"Enter updated verification code in box and press submit.")
                self.logger.info(u"{0:=^130}".format(""))
                self.logger.info(u"{0:=^130}".format(""))
                #self.appleAPI = None
                self.triggerCheck2fa()
                return 2, self.appleAPI
            # 2 = 2fa required
            #self.appleAPI = self.self.appleAPI
            if self.debugicloud:
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'type self.appleAPI result equals:')
                self.logger.debug(str(type(self.appleAPI)))
                #self.logger.debug(u'self.appleAPI.devices equals:')
                #self.logger.debug(str(self.appleAPI.devices))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'self.appleAPI.friends.details equals:')
                self.logger.debug(str(self.appleAPI.friends.details))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'self.appleAPI.friends.locations equals:')
                self.logger.debug(str(self.appleAPI.friends.locations))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'Type of self.appleAPI.friends.locations equals:')
                self.logger.debug(str(type(self.appleAPI.friends.locations)))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'Type of self.appleAPI.friends.data')
                self.logger.debug(str(type(self.appleAPI.friends.data)))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'self.appleAPI.friends.data equals')
                self.logger.debug(str(self.appleAPI.friends.data))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'self.appleAPI.friends.data[followers] equals:')
                self.logger.debug(str(self.appleAPI.friends.data['followers']))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))

                follower = self.appleAPI.friends.data['followers']
                self.logger.debug(u'follower or self.appleAPI.friends.data[followers] equals:')
                for fol in follower:
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u"{0:=^130}".format(""))
                    self.logger.debug(u'Follower in follower: ID equals')
                    self.logger.debug(str(fol['id']))
                    self.logger.debug(u'email address from Id equals:')
                    self.logger.debug(str(fol['invitationFromEmail']))

                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u'self.appleAPI.friends.details equals:')
                self.logger.debug(str(self.appleAPI.friends.details))
                self.logger.debug(u"{0:=^130}".format(""))
                self.logger.debug(u"{0:=^130}".format(""))
            return 0, self.appleAPI

        except PyiCloudFailedLoginException:
            self.logger.error(u'Login failed - Check username/password - has it changed recently?. ')
            self.appleAPI = None
            self.allDevicesOffline()
            return 1, 'NL'

        except PyiCloud2SARequiredException:
            self.logger.error(u'Login failed.  Account requires 2nd factor, verification code setup.  Please see config window')
            self.requires2FA = True
            self.appleAPI = None
            self.allDevicesOffline()
            self.triggerCheck2fa()
            return 1, 'NL'

        except ValueError as e:
            self.logger.error(u"{0:=^130}".format(""))
            self.logger.error(u'Login failed - 2FA Authenication is supported. ')
            self.logger.debug(u'Error Given is:'+str(e)+str(e.__dict__))
            self.logger.error(u"{0:=^130}".format(""))
            self.allDevicesOffline()
            return 1, 'NL'

        except PyiCloudAPIResponseException as e:
            self.logger.debug(u'Login Failed API Response Error.   ' + str(e) + str(e.__dict__))
            self.logger.debug(e)
            if e.code in [450,421,500]:
                self.logger.info("Error Code 450/421/500 Given: Re-authentication seems to be required.  Reauthenicating now.")
                self.appleAPI.authenticate(True)
                try:
                    self.logger.debug(u"Testing ********************************************")
                    self.logger.debug( self.appleAPI.devices[0].location() )
                    self.logger.debug(u"********************************************")
                    return 0, self.appleAPI
                except PyiCloudAPIResponseException:
                    self.logger.debug("Could not re-authenticate at all... Sorry.")
                    self.appleAPI = None
                    self.allDevicesOffline()
                    return 1, 'NI'
            return 1, 'NI'

        except Exception as e:
            self.logger.debug(u'Login Failed General Error.   ' + str(e) + str(e.__dict__))
            self.logger.info(u"Issue connecting to icloud.  ?Internet issue, or temp icloud server down...")
            self.logger.debug(e)
            return 1, 'NI'

    def deleteAccount(self,valuesDict):
        self.logger.debug(u'deleteAccount Button pressed Called.')
        self.appleAPI = None
        self.pluginPrefs['appleAPIid'] = ""
        valuesDict['appleAPIid'] =""
        valuesDict['appleId'] = ""
        valuesDict['applePwd'] = ""
        valuesDict['verficationcode'] = ""

        indigoPreferencesPluginDir = indigo.server.getInstallFolderPath()+"/Preferences/Plugins/" + self.pluginId + "/"

        self.logger.info("Deleting Session data from:"+str(indigoPreferencesPluginDir))

        files = glob.glob(indigoPreferencesPluginDir+"/session/*")
        for f in files:
            self.logger.info("Deleting file:"+(str(f)))
            try:
                os.remove(f)
            except OSError:
                pass
        files2 = glob.glob(indigoPreferencesPluginDir+"/*")
        for fi in files2:
            self.logger.info("Deleting file:"+(str(fi)))
            try:
                os.remove(fi)
            except OSError:
                pass

        return valuesDict


    def loginAccount(self, valuesDict):
        self.logger.debug(u'loginAccount Button pressed Called.')
        self.validatePrefsConfigUi(valuesDict)
        self.logger.debug(u"Using Details: Username:"+str(valuesDict['appleId'])+u" and password:"+str(valuesDict['applePwd']))
        self.appleAPI = None
        self.pluginPrefs['appleAPIid']= ""
        self.logger.info(u"{0:=^130}".format(""))
        self.logger.info(u'Attempting Login to Apple Account:'+str(valuesDict['appleId']))


        valuesDict['appleAPIid']=''
        iLogin = self.iAuthorise(valuesDict['appleId'], valuesDict['applePwd'])
        if self.appleAPI != None:
            self.logger.info(u"Account username and password has been verifed by Apple")
            if self.appleAPI.requires_2fa==False:
                self.logger.info(u"Two Factor Authenication (2FA) is NOT enabled on this account")
                self.logger.info(u"OR this Computer/Device is a Trusted Session.  Hence Code not needed")
                self.logger.info(u"This is the ideal setup for iFindFriends")
                self.logger.info(u"Nothing further is required and the account should be functioning")
                self.logger.info(u"Please select options and press Save.")
            else:
                self.logger.info(u"Two Factor Authenication (2FA) is enabled on this account")
                self.logger.info(u"Please enable the use 2FA checkbox to continue.")
                self.logger.info(u"Another device from this account is required to verify the account")
                self.logger.info(u"From this other device please approve and enter the code displayed")
                self.logger.info(u"Once Code is enter press Submit Code button")
            self.logger.debug(u"Account Requires 2FA to continue = "+str(self.appleAPI.requires_2fa))
            self.logger.info(u"{0:=^130}".format(""))
            self.requires2FA = self.appleAPI.requires_2fa
        return valuesDict

    def submitCode(self,valuesDict):
        self.logger.debug(u'submit Code Button pressed Called.')
        vercode = valuesDict['verficationcode']
        if vercode is None:
            self.logger.error("Please enter code")
            return

        validcode = self.appleAPI.validate_2fa_code(vercode)

        if validcode == False:
            self.logger.error("Code Error:  Please try again...")
            return
        else:
            self.logger.info("Verification Code Accepted.")
            self.requires2FA = False
            valuesDict['appleAPIid'] = valuesDict['appleId']
            self.pluginPrefs['appleAPIid'] = valuesDict['appleId']
            self.logger.info(u"Trusted Session:"+str(self.appleAPI.is_trusted_session))

        if not self.appleAPI.is_trusted_session:
            self.logger.info("Session is not Trusted. Requesting Trust...")
            result = self.appleAPI.trust_session()
            self.logger.info("Session Trust Result:"+ str(result))
        return valuesDict


    def urlGenerate(self, latitude, longitude, mapAPIKey, iHorizontal, iVertical, iZoom, dev):
        ################################################
        # Modified by FindiStuff
        # Routine generate a Static Google Maps HTML URL request
        # for a single device
        # Map size is based on the zoom parameter passed or defaults to level 15 (street names)
        # All commands are of the format...
        # https://maps.googleapis.com/maps/api/staticmap?parameters where the parameters
        # Determine the map content and format
        # Parameters are separated with the & symbol
        # Need to take care of the piping symbol
        # url pipe = %7C
        try:
            self.logger.debug('** Device being mapped is:' + str(latitude) + ' ' + str(longitude))
            mapLabel =  dev.pluginProps.get('mapLabel','lightblue1')
            # Create Map url
            mapCentre = 'center=' + str(latitude) + "," + str(longitude)

            # Set size
            if self.mapType=='google':
                if iZoom < 0:
                    iZoom = 0
                elif iZoom > 21:
                    iZoom = 21
                if iHorizontal > 640:
                    iHorizontal = 640
                elif iHorizontal < 50:
                    iHorizontal = 50
                if iVertical > 640:
                    iVertical = 640
                elif iVertical < 50:
                    iVertical = 50
                mapAPIKey = self.googleAPI

            if 'Bing' in self.mapType:
                if iZoom < 0:
                    iZoom = 0
                elif iZoom > 20:
                    iZoom = 20
                mapAPIKey = self.BingAPI

            mapZoom = 'zoom=' + str(iZoom)

            mapSize = 'size=' + str(iHorizontal) + 'x' + str(iVertical)
            mapFormat = 'format=jpg&maptype=hybrid'
            # Use a standard marker for a GeoFence Centre
            mapMarkerGeo = "markers=color:blue%7Csize:mid%7Clabel:G"
            mapMarkerPhone = "markers=icon:http://chart.apis.google.com/chart?chst=d_map_pin_icon%26chld=mobile%257CFF0000%7C" + str(
                latitude) + "," + str(longitude)
            mapGoogle = 'https://maps.googleapis.com/maps/api/staticmap?'
            #urlmapGoogle = 'https://www.google.com/maps/@?api=1&map_action=map&center='+str(latitude)+','+str(longitude)+'&zoom='+str(iZoom)+'&basemap=satellite'
            urlmapGoogle = 'comgooglemaps://maps.google.com/maps?z='+str(iZoom)+'&t=h&q=' + str(latitude) + ',' + str(longitude)
            #Remove API usage altogether
            customURL = mapGoogle + mapCentre + '&' + mapZoom + '&' + mapSize + '&' + mapFormat + '&' + mapMarkerGeo + '&' + mapMarkerPhone + '&key=' + mapAPIKey
            self.logger.debug(u'StaticMap URL equals:'+str(customURL))
            self.logger.debug(u'Map URL equals:' + str(urlmapGoogle))

            mapOSM = 'http://staticmap.openstreetmap.de/staticmap.php?center='+str(latitude)+','+str(longitude)+'&'+str(mapZoom)+'&' + mapSize + '&markers='+str(latitude)+','+str(longitude)+','+str(mapLabel)

            if self.mapType =='arcgisWorld2d' or 'Bing' in self.mapType or self.mapType=='arcgisWorldImagery' or self.mapType=='arcgisWorldStreetMap' or self.mapType=='arcgisWorldImageryHybrid' or self.mapType=='maps.six':
                latitude = float(latitude)
                longitude = float(longitude)
                # Fudge a similar zoom
                zoomFactor = 0.0005 * iZoom
                toplatitude = latitude- zoomFactor
                toplongitude = longitude - zoomFactor
                bottomlatitude = latitude + zoomFactor
                bottomlongitude = longitude +zoomFactor
                if self.mapType=='arcgisWorld2d':
                    mapWorld2d = 'https://services.arcgisonline.com/arcgis/rest/services/ESRI_Imagery_World_2D/MapServer/export?bbox='+str(toplongitude)+','+str(toplatitude)+','+str(bottomlongitude)+','+str(bottomlatitude)+'&bboxSR=4326'+'&size='+ str(iHorizontal) + ',' + str(iVertical) +'&f=image'
                if self.mapType == 'arcgisWorldImagery':
                    mapWorld2d = 'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export?bbox=' + str(toplongitude) + ',' + str(toplatitude) + ',' + str(bottomlongitude) + ',' + str(bottomlatitude) + '&bboxSR=4326' + '&size=' + str(iHorizontal) + ',' + str(iVertical) + '&f=image' + '&markers=color:purple|'+str(latitude)+','+str(longitude)
                if self.mapType == 'arcgisWorldStreetMap':
                    mapWorld2d = 'https://services.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer/export?bbox=' + str(
                        toplongitude) + ',' + str(toplatitude) + ',' + str(bottomlongitude) + ',' + str(
                        bottomlatitude) + '&bboxSR=4326' + '&size=' + str(iHorizontal) + ',' + str(iVertical) + '&f=image'
                if self.mapType == 'maps.six':
                    mapWorld2d = 'http://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Imagery/MapServer/export?bbox=' + str(
                        toplongitude) + ',' + str(toplatitude) + ',' + str(bottomlongitude) + ',' + str(
                        bottomlatitude) + '&bboxSR=4326' + '&size=' + str(iHorizontal) + ',' + str(iVertical) + '&f=image'
                if 'Bing' in self.mapType:
                    mapWorld2d = 'http://bing.com/maps/embed?cp=' + str(latitude) + '~' + str(longitude) + "&h="+str(iVertical)+ "&w="+str(iHorizontal)
                    BingStatic = 'http://dev.virtualearth.net/REST/v1/Imagery/Map'
                    
                    if 'Satellite' in self.mapType:
                        mapWorld2d = mapWorld2d + "&style=h"
                        if 'SatelliteWO' in self.mapType:
                            BingStatic = BingStatic + "/Aerial"
                        else:
                            BingStatic = BingStatic + "/AerialWithLabels"
                    elif 'Road' in self.mapType:
                        mapWorld2d = mapWorld2d + "&style=r"
                        BingStatic = BingStatic + '/Road'
                    elif 'Gray' in self.mapType:
                        mapWorld2d = mapWorld2d + "&style=r"
                        BingStatic = BingStatic + '/CanvasGray'
                    elif 'BirdsEye' in self.mapType:
                        mapWorld2d = mapWorld2d + "&style=h"
                        BingStatic = BingStatic + '/BirdsEyeV2'
                    elif 'Canvas' in self.mapType:
                        mapWorld2d = mapWorld2d + "&style=r"
                        BingStatic = BingStatic + '/CanvasLight'

                    mapWorld2d= mapWorld2d + "&lvl="+str(iZoom)
                    BingStatic = BingStatic + '/'+ str(latitude) + "," + str(longitude) + "/" + str(iZoom)+ "?mapsize="+str(iHorizontal)+","+str(iVertical)
                    if 'Roads' in self.mapType or 'Canvas' in self.mapType:
                        BingStatic = BingStatic + '&mapLayer=Basemap,Buildings'
                    BingStatic = BingStatic + "&key="+self.BingAPI

                    

            if self.mapType=='google':
                return customURL, urlmapGoogle
            elif self.mapType=='openstreetmap':
                return mapOSM, urlmapGoogle
            elif self.mapType =='arcgisWorld2d' or self.mapType=='arcgisWorldImagery' or self.mapType=='arcgisWorldStreetMap' or self.mapType=='maps.six':
                return mapWorld2d, urlmapGoogle
            elif 'Bing' in self.mapType:
                return BingStatic, mapWorld2d
            else:
                return 0,0


        except Exception as e:
            self.logger.info(u'Mapping Exception/Error:'+str(e))


    def urlAllGenerate(self, mapAPIKey, iHorizontal, iVertical, iZoom):

        ################################################
        # from FindiStuff
        # Routine generate a Static Google Maps HTML URL request
        # for all devices
        # Map size is automatically calculated based on the two furthest points (devices and/or geofences)
        # All commands are of the format...
        # https://maps.googleapis.com/maps/api/staticmap?parameters where the parameters
        # Determine the map content and format
        # Parameters are separated with the & symbol
        # Need to take care of the piping symbol
        # url pipe = %7C

     #   global iDebug1, iDebug2, iDebug3, iDebug4, iDebug5, gIcon

        # Create geoFence list
        try:

            if self.mapType=='google':
                # Create Map url
                # URL Centre and Zoom is calculated by Google Maps
                mapCentre = ''
                # Set zoom
                mapZoom = ''
                # Set size
                if iHorizontal>640:
                    iHorizontal=640
                elif iHorizontal<50:
                    iHorizontal=50
                if iVertical>640:
                    iVertical=640
                elif iVertical<50:
                    iVertical=50
                mapSize='size='+str(iHorizontal)+'x'+str(iVertical)
                mapFormat='format=jpg&maptype=hybrid'
                # Use a standard marker for a GeoFence Centre
                mapMarkerGeo = "markers=color:blue%7Csize:mid%7Clabel:G"
                # Now create the device markers (must be a maximum of 5 different types and less than 64x64 and on a http: server)
                mapMarkerP = ''
                mapMarkerPhone = ''
                for dev in indigo.devices.iter('self.FindFriendsFriend'):
                    mapMarkerP = "markers=icon:http://chart.apis.google.com/chart?chst=d_map_pin_icon%26chld=mobile%257CFF0000%7C"+\
                                     str(dev.states['latitude'])+","+str(dev.states['longitude'])
                    # Store the custom marker
                    mapMarkerPhone = mapMarkerPhone+'&'+mapMarkerP

                if len(mapMarkerPhone)<2:
                    #Trap no devices
                    mapMarkerPhone = ''
                mapGoogle = 'https://maps.googleapis.com/maps/api/staticmap?'
                #if mapAPIKey == 'No Key':
                customURL = mapGoogle+mapCentre+'&'+mapZoom+'&'+mapSize+'&'+mapFormat+'&'+mapMarkerGeo+'&'+mapMarkerPhone+ '&key=' + mapAPIKey
                #else:
                #   customURL = mapGoogle+mapCentre+'&'+mapZoom+'&'+mapSize+'&'+mapFormat+'&'+mapMarkerGeo+'&'+mapMarkerPhone+'&key='+mapAPIKey
                return customURL

        except Exception as e:
            self.logger.info(u'urlAllGenerate'+str(e))
            return ''

    def useWaze(self, lat, long, endlat, endlong):
        try:
            from_loc = str(lat) + "," + str(long)
            to_loc = str(endlat) + "," + str(endlong)
            route = WazeRouteCalculator.WazeRouteCalculator(from_loc, to_loc, self.wazeRegion)
            route_time, route_distance = route.calc_route_info()
            timedisplay = str('Time %.2f minutes.' % route_time)

            if self.wazeUnits == "km":
                distancedisplay = str('Distance %.2f km.' % route_distance)
            else:
                route_distance = route_distance / 1.609344
                distancedisplay = str('Distance %.2f miles.' % route_distance)

            route_time = round(route_time, 0)
            route_distance = round(route_distance, 2)

            return timedisplay, distancedisplay, route_time, route_distance

        except WazeRouteCalculator.WRCError as err:
            self.logger.debug("Waze Error: "+str(err))
            return "unknown","unknown",0,0
        except Exception as e:
            self.logger.debug("Caught Exception in using Waze Route Calculator:"+str(e))

            return "unknown","unknown",0,0



    def checkHomeOther(self):

        try:
            self.logger.debug('Check HomeOther Called..')
            # need to start with GeofFence and then go through all devices
            # iDevName = dev.states['friendName']
            # Check GeoFences after devices


            #
            # if len(self.googleAPI) <5:
            #     self.logger.info(u"{0:=^130}".format(""))
            #     self.logger.info(u'Need to enter and approve GoogleAPI key for distance calculation')
            #     self.logger.info(u"{0:=^130}".format(""))
            #     return

            for geoDevices in indigo.devices.iter('self.FindFriendsGeofence'):
                if geoDevices.enabled:
                    igeoFriendsRange = 0
                    localProps = geoDevices.pluginProps
                    if not 'geoName' in localProps:
                        continue
                    igeoName = localProps['geoName']
                    # If home Geo updates all devices time/distance
                    if igeoName == 'Home':
                        igeoLong = float(localProps['geoLongitude'])
                        igeoLat = float(localProps['geoLatitude'])
                        igeoRangeDistance = int(localProps['geoRange'])
                        igeoFriendsRangeOld = int(geoDevices.states['friendsInRange'])
                        for dev in indigo.devices.iter("self.myDevice"):
                            # add check here make sure dev is Online before checking details of GeoFences
                            if dev.enabled and dev.states['deviceIsOnline'] == True:
                                self.logger.debug('Home Check Details on check:' + str(igeoName) + ' For Friend:' + str(dev.name))
                                iDevLatitude = float(dev.states['latitude'])
                                iDevLongitude = float(dev.states['longitude'])
                                # Now check the distance for each device
                                # Calculate the distance
                                self.logger.debug('Point 1' + ' ' + str(igeoLat) + ',' + str(igeoLong) + ' Point 2 ' + str(
                                    iDevLatitude) + ',' + str(iDevLongitude))

                                timedisplay, distancedisplay, route_time, route_distance =  self.useWaze(iDevLatitude,iDevLongitude,igeoLat, igeoLong)
                                if timedisplay != "unknown":
                                    dev.updateStateOnServer('homeDistanceText', value=distancedisplay)
                                    dev.updateStateOnServer('homeTimeText', value=timedisplay)
                                    dev.updateStateOnServer('homeDistance', value=route_distance )
                                    dev.updateStateOnServer('homeTime', value=route_time)
                        #This is home Geo - now update all devices
                        for dev in indigo.devices.iter("self.FindFriendsFriend"):
                            # add check here make sure dev is Online before checking details of GeoFences
                            if dev.enabled and dev.states['deviceIsOnline'] == True:
                                self.logger.debug('Home Check Details on check:' + str(igeoName) + ' For Friend:' + str(dev.name))
                                iDevLatitude = float(dev.states['latitude'])
                                iDevLongitude = float(dev.states['longitude'])
                                # Now check the distance for each device
                                # Calculate the distance
                                self.logger.debug('Point 1' + ' ' + str(igeoLat) + ',' + str(igeoLong) + ' Point 2 ' + str(
                                    iDevLatitude) + ',' + str(iDevLongitude))
                                timedisplay, distancedisplay, route_time, route_distance =  self.useWaze(iDevLatitude,iDevLongitude,igeoLat, igeoLong)
                               # texttodisplay = str('Time %.2f minutes, distance %.2f km.' % route_time, route_distance)
                                if timedisplay != "unknown":
                                    dev.updateStateOnServer('homeDistanceText', value=distancedisplay)
                                    dev.updateStateOnServer('homeTimeText', value=timedisplay)
                                    dev.updateStateOnServer('homeDistance', value=route_distance )
                                    dev.updateStateOnServer('homeTime', value=route_time)

                    if igeoName == 'Other':
                        igeoLong = float(localProps['geoLongitude'])
                        igeoLat = float(localProps['geoLatitude'])
                        igeoRangeDistance = int(localProps['geoRange'])
                        igeoFriendsRangeOld = int(geoDevices.states['friendsInRange'])

                        # This is home Geo - now update all devices
                        for dev in indigo.devices.iter("self.FindFriendsFriend"):
                            if dev.enabled and dev.states['deviceIsOnline'] == True:
                                self.logger.debug(
                                    'Other Geo Check Details on check:' + str(igeoName) + ' For Friend:' + str(dev.name))
                                iDevLatitude = float(dev.states['latitude'])
                                iDevLongitude = float(dev.states['longitude'])
                                # Now check the distance for each device
                                # Calculate the distance
                                self.logger.debug('Point 1' + ' ' + str(igeoLat) + ',' + str(igeoLong) + ' Point 2 ' + str(
                                    iDevLatitude) + ',' + str(iDevLongitude))

                                timedisplay, distancedisplay, route_time, route_distance =  self.useWaze(iDevLatitude,iDevLongitude,igeoLat, igeoLong)

                                if timedisplay != "unknown":
                                    dev.updateStateOnServer('otherDistanceText', value=distancedisplay)
                                    dev.updateStateOnServer('otherTimeText', value=timedisplay)
                                    dev.updateStateOnServer('otherDistance', value=route_distance)
                                    dev.updateStateOnServer('otherTime', value=route_time)

                        for dev in indigo.devices.iter("self.myDevice"):
                            if dev.enabled and dev.states['deviceIsOnline'] == True:
                                self.logger.debug(
                                    'Other Geo Check Details on check:' + str(igeoName) + ' For Friend:' + str(dev.name))
                                iDevLatitude = float(dev.states['latitude'])
                                iDevLongitude = float(dev.states['longitude'])
                                # Now check the distance for each device
                                # Calculate the distance
                                self.logger.debug('Point 1' + ' ' + str(igeoLat) + ',' + str(igeoLong) + ' Point 2 ' + str(
                                    iDevLatitude) + ',' + str(iDevLongitude))

                                timedisplay, distancedisplay, route_time, route_distance =  self.useWaze(iDevLatitude,iDevLongitude,igeoLat, igeoLong)

                                if timedisplay != "unknown":
                                    dev.updateStateOnServer('otherDistanceText', value=distancedisplay)
                                    dev.updateStateOnServer('otherTimeText', value=timedisplay)
                                    dev.updateStateOnServer('otherDistance', value=route_distance)
                                    dev.updateStateOnServer('otherTime', value=route_time)
        except Exception as e:
            self.logger.exception(u'Error Within checkHomeOther:')
            return

    def iConvertMeters(self, meters):
        self.logger.debug('iConvertMeters Called')
        try:
            texttoreturn = ''
            if meters >= 1000:
                result = int(meters/1000)
                texttoreturn = str(result)+' kms '
                # remove the Km from the distance
                result = int(meters - result*1000)
            else:
                result = int(meters)

            texttoreturn = texttoreturn +str(result) +' meters'
            return texttoreturn
        except:
            self.logger.exception('iCovertMeters Exception')
            return 'Unknown'

    # def iConvertMetersTime(self, meters):
    #     self.logger.debug('iConvertMetersTime Called')
    #     try:
    #         texttoreturn = ''
    #         secondsoftime = int(meters/float(self.travelTime))
    #         hours, remainder = divmod(secondsoftime, 3600)
    #         minutes, seconds = divmod(remainder, 60)
    #         if hours>0:
    #             texttoreturn = '%s hr(s) %s minutes' % (hours, minutes)
    #         else:
    #             texttoreturn = '%s minutes' % (minutes)
    #         return texttoreturn, secondsoftime
    #     except:
    #         self.logger.exception('iCovertMetersTime Exception:  Is Plugin Config probably setup? Is Travel Time a number?')
    #
    #         return 'Unknown', 'Unknown'


    def iDistance(self, lat1, long1, lat2, long2):

        ################################################
        # Once again thanks Mike and iFindStuff!
        # Calculates the 'As the crow flies' distance between
        # two points and returns value in metres
        # First check if numbers are valid
        if lat1+long1 == 0.0 or lat2+long2 == 0.0:

            #  Zero default sent through
            self.logger.info(u'No distance calculation possible as values are 0,0,0,0')
            return False, 0.0

        # Convert latitude and longitude to
        # spherical coordinates in radians.
        degrees_to_radians = math.pi/180.0

        # phi = 90 - latitude
        phi1 = (90.0 - lat1)*degrees_to_radians
        phi2 = (90.0 - lat2)*degrees_to_radians

        # theta = longitude
        theta1 = long1*degrees_to_radians
        theta2 = long2*degrees_to_radians

        # Compute spherical distance from spherical coordinates.

        # For two locations in spherical coordinates
        # (1, theta, phi) and (1, theta', phi')
        # cosine( arc length ) =
        #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
        # distance = rho * arc length

        cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
               math.cos(phi1)*math.cos(phi2))
        try:
            arc = math.acos( cos )
        except Exception as e:
            self.logger.debug('Expected Error within iDistance Calculation: Cos Equals:'+str(cos) +' Exception Caught:'+str(e))
            arc = 1
            pass
        # Remember to multiply arc by the radius of the earth
        # e.g. m to get actual distance in m
        mt_radius_of_earth = 6373000.0
        distance = arc * mt_radius_of_earth

        return True, int(distance)

    # def distanceCalculation(self, origin, final, APIKey, mode='driving',units="metric"):
    #
    #     ################################################
    #     # Uses Google Maps Distance Matrix API to calculate travel distance and time.
    #     # Note that output is in km or m that must be converted to current units.
    #     # Limited to 2.500 uses/day and plugin restricts to 10 min frequency/device
    #
    #     self.logger.debug(u'distanceCalculation run')
    #
    #
    #     try:
    #         gmaps = googlemaps.Client(APIKey)
    #     except:
    #
    #         self.logger.info(u"{0:=^130}".format(""))
    #         self.logger.info(u'Google API Connection Error.')
    #         self.logger.info(u'Incorrect API.  Have you obtained you free Google API Key?')
    #         self.logger.info(u'Or Key not approved for both Static Maps API and Distance Matrix API access')
    #         self.logger.info(u'Check forum for details on how to authorise key for both APIs')
    #         self.logger.info(u"{0:=^130}".format(""))
    #         return 'FailAPI','',''
    #
    #     try:
    #         now = datetime.datetime.now()
    #         distance_result = gmaps.distance_matrix(origin,final,
    #                                                 mode='driving', language=None, avoid=None, units='metric', departure_time=now,
    #                                                 arrival_time=None, transit_mode=None, transit_routing_preference=None)
    #         if self.debugdistance:
    #             self.logger.debug(u'Distance Result from Google:')
    #             self.logger.debug(str(distance_result))
    #
    #         iTimeTaken = distance_result['rows'][0]['elements'][0]['duration']['text']
    #         iTimeTakenseconds = distance_result['rows'][0]['elements'][0]['duration']['value']
    #
    #         iDistCalc = distance_result['rows'][0]['elements'][0]['distance']['text']
    #         iDistCalcmeters = distance_result['rows'][0]['elements'][0]['distance']['value']
    #
    #         return iTimeTaken, iTimeTakenseconds, iDistCalc, iDistCalcmeters
    #
    #     except ApiError:
    #         self.logger.info(u"{0:=^130}".format(""))
    #         self.logger.info(u'Google API Connection Error.')
    #         self.logger.info(u'Incorrect API.  Have you obtained your free Google API key?')
    #         self.logger.info(u'or Key not approved for both Static Maps API and Distance Matrix API access')
    #         self.logger.info(u'Check forum for details on how to authorise key for both APIs')
    #         self.logger.info(u"{0:=^130}".format(""))
    #         return 'FailAPI','','',''
    #
    #     except Exception as e:
    #         self.logger.exception(u'Problem with distance Calculation')
    #         return 'FailAPI','','',''


##################  Trigger

    def triggerStartProcessing(self, trigger):
        self.logger.debug("Adding Trigger %s (%d) - %s" % (trigger.name, trigger.id, trigger.pluginTypeId))
        assert trigger.id not in self.triggers
        self.triggers[trigger.id] = trigger

    def triggerStopProcessing(self, trigger):
        self.logger.debug("Removing Trigger %s (%d)" % (trigger.name, trigger.id))
        assert trigger.id in self.triggers
        del self.triggers[trigger.id]

    def triggerCheck2fa(self):
        self.logger.debug("Checking trigger as 2FA state called")
        for triggerId, trigger in sorted(self.triggers.items()):
            self.logger.debug("Checking Trigger (%s), Type: %s, Friend: %s, and event : %s" % (trigger.name, trigger.id, trigger.pluginTypeId))
            # self.logger.error(str(trigger))
            if trigger.pluginTypeId == "account2FAneeded" :
                # 2fa failed
                # send trigger.
                self.logger.debug("======== Executing Trigger %s (%d)" % (trigger.name, trigger.id))
                indigo.trigger.execute(trigger)

    def triggerCheck(self, device, friend, triggertype):

        self.logger.debug('triggerCheck run.  device.id:'+str(device.id)+' friend:'+str(friend)+' triggertype:'+str(triggertype))
        try:

            if self.startingUp:
                self.logger.info(u'Trigger: Ignore as FindFriendsMini Just started.')
                return

            ## don't trigger if device is offline.
            # Device swapping between online and offline can remove & add to Geofence
            # This will capture the exit
            # Should check higher in code as well - but no harm? leaving this here.

            if device.states['deviceIsOnline'] == False:
                self.logger.debug(u'Trigger Cancelled as Device is Not Online')
                return

            for triggerId, trigger in sorted(self.triggers.items()):

                self.logger.debug("Checking Trigger %s (%s), Type: %s, Friend: %s, and event : %s" % (trigger.name, trigger.id, trigger.pluginTypeId, friend, triggertype))
                #self.logger.error(str(trigger))

                if trigger.pluginTypeId =='account2FAneeded':  ## selected a 2FA triggertype
                    if triggertype=='account2FAneeded':
                    # 2fa failed
                    # send trigger.
                        self.logger.debug("======== Executing Trigger %s (%d)" % (trigger.name, trigger.id))
                        indigo.trigger.execute(trigger)
                        continue
                    else:
                        self.logger.debug("Skipping further checks as this is a 2FA trigger.")
                        continue

                if trigger.pluginProps["geofenceId"] != str(device.id) or (trigger.pluginTypeId == "geoFenceExit" and triggertype !='EXIT') or (trigger.pluginTypeId == "geoFenceEnter" and triggertype !='ENTER'):
                    self.logger.debug("Skipping Trigger %s (%s), wrong device: %s, or friend: %s,  or event : %s" % (trigger.name, trigger.id, device.id, friend, triggertype))
                    #self.logger.debug(u'or Checked Trigger Wrong event.  '+str(triggertype))
                else:
                    idfriend = ''
                    # get id from name
                    # could save id to save this iteration but ugly looking and less useful display
                    # get indigo device name
                    # realised could save iteration here by finding name of device of current trigger via looking up name via indigodevice Id
                    # quicker than iterating through all devices looking for mathcing name
                    if (int(trigger.pluginProps['friendId'] ) in indigo.devices):
                        triggerdevice = indigo.devices[int(trigger.pluginProps['friendId'] )]
                        triggerdeviceFriendName = triggerdevice.pluginProps['friendName']
                        self.logger.debug(u'Trigger device friendName is: '+str(triggerdeviceFriendName))
                    else:
                        self.logger.info("Device Key ID not longer exists. Skipping")
                        continue
                    #self.logger.debug(triggerdevice)

                    if triggerdevice.enabled:
                        if str(friend) == str(triggerdeviceFriendName):
                            self.logger.debug(u'Matching friend found:'+str(triggerdeviceFriendName)+' and trigger needed is:'+str(friend))
                            idfriend = triggerdevice.id

                    #for dev in indigo.devices.iter("self.FindFriendsFriend"):
                    #    if dev.enabled:
                     #       iDevUniqueName = dev.pluginProps['friendName']
                     #       if iDevUniqueName == friend:
                    #            self.logger.debug(u'Matching friend found:'+str(friend)+' id is :'+str(dev.id))
                    #
                    if idfriend=='':
                        self.logger.debug(u'Trigger Does not  match friend :'+str(friend)+' to TriggerFriend Needed:'+str(triggerdeviceFriendName))
                        continue #back to check other triggers

                    ## don't trigger if device is offline.
                    # Device swapping between online and offline can remove add to Geofence
                    # This will capture the exit
                    # Should check higher in code as well - but no harm? leaving this here.

                    if device.states['deviceIsOnline'] == False:
                        self.logger.debug(u'Trigger Cancelled as Device is Not Online')


                    if trigger.pluginTypeId == "geoFenceExit" and triggertype=='EXIT':
                        self.logger.debug("===== Executing Trigger %s (%d)" % (trigger.name, trigger.id))
                        indigo.trigger.execute(trigger)
                    elif trigger.pluginTypeId == "geoFenceEnter" and triggertype=='ENTER':
                        self.logger.debug("======== Executing Trigger %s (%d)" % (trigger.name, trigger.id))
                        indigo.trigger.execute(trigger)
                    else:
                        self.logger.debug("Not Run Trigger Type %s (%d), %s" % (trigger.name, trigger.id, trigger.pluginTypeId))

        except:
            self.logger.exception(u'Caught Exception within Trigger Check')
            return


