#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
FindFriendsMini
Authors: See (repo)

Logons on to icloud account and access friends information for creation of indigo Devices

Enormously based on FindiStuff by Chameleon and GhostXML by DaveL17

"""

# Stock imports


try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except Exception as e:
    pass
    #o.server.log(u'error in import locales')

import sys
import math

import time as t

try:
    import indigo
except ImportError:
    pass

try:
    from pyicloud import PyiCloudService
    #from pyicloud.exceptions import PyiCloudFailedLoginException

    from pyicloud.exceptions import (
        PyiCloudFailedLoginException,
        PyiCloudAPIResponseError,
        PyiCloud2SARequiredError,
        PyiCloudServiceNotActivatedErrror
    )


except:
    indigo.server.log("FATAL ERROR - Cannot find pyicloud - check with developer")
    indigo.server.log("Can't find pyicloud for more details and how to resolve."
                      "Alternatively - check the name of the plugin in the Plugins folder.  Is is FindFriendsMini.pluginIndigo"
                      "or FindFriendsMini(1).pluginIndigo?  Make sure that all FindFriendsMini files are deleted from Downloads"
                      "before downloading the latest versions")

# Now the HTTP and Compatibility libraries
try:
    import requests
except:
    indigo.server.log("Note: requests.py must be installed for this plugin to operate.  Indigo 7 ONLY.  See the forum")
    indigo.server.log(
        "Alternatively - check the name of the plugin in the Plugins folder.  Is is FindFriendsMini.pluginIndigo"
        "or FindFriendsMini(1).pluginIndigo?  Make sure that all FindFriendsMini files are deleted from Downloads"
        "before downloading the latest versions")

# Date and time libraries
import time

try:
    import pydevd
except ImportError:
    pass

import webbrowser
import os

from ghpu import GitHubPluginUpdater

global accountOK
global appleAPI

# Custom imports
#import iterateXML

__author__ = u"GlennNZ"
__build__ = u""
__copyright__ = u"There is no copyright for the code base."
__license__ = u"MIT"
__title__ = u"FindFriendsMini Plugin for Indigo Home Control"
__version__ = u"0.0.8"

# Establish default plugin prefs; create them if they don't already exist.
kDefaultPluginPrefs = {
    u'configMenuServerTimeout': "15",  # Server timeout limit.
    u'showDebugInfo': False,  # Verbose debug logging?
    u'showDebugLevel': "1",  # Low, Medium or High debug output.
    u'updaterEmail': "",  # Email to notify of plugin updates.
    u'updaterEmailsEnabled': False  # Notification of plugin updates wanted.
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        """ docstring placeholder """
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False
        self.prefsUpdated = False
        indigo.server.log(u"")
        indigo.server.log(u"{0:=^130}".format(" Initializing New Plugin Session "))
        indigo.server.log(u"{0:<30} {1}".format("Plugin name:", pluginDisplayName))
        indigo.server.log(u"{0:<30} {1}".format("Plugin version:", pluginVersion))
        indigo.server.log(u"{0:<30} {1}".format("Plugin ID:", pluginId))
        indigo.server.log(u"{0:<30} {1}".format("Indigo version:", indigo.server.version))
        indigo.server.log(u"{0:<30} {1}".format("Python version:", sys.version.replace('\n', '')))
        indigo.server.log(u"{0:=^130}".format(""))

        self.debug = self.pluginPrefs.get('showDebugInfo', False)
        self.debugLevel = int(self.pluginPrefs.get('showDebugLevel', 1))
        self.logFile = u"{0}/Logs/com.GlennNZ.indigoplugin.FindFriendsMini/plugin.log".format(
            indigo.server.getInstallFolderPath())
        self.configMenuTimeCheck = int(self.pluginPrefs.get('configMenuTimeCheck', "5"))
        #self.updater = indigoPluginUpdateChecker.updateChecker(self, "http://")
        self.updaterEmailsEnabled = self.pluginPrefs.get('updaterEmailsEnabled', False)

        self.updateFrequency = float(self.pluginPrefs.get('updateFrequency', "24")) * 60.0 * 60.0
        self.next_update_check = time.time()
        self.configVerticalMap = self.pluginPrefs.get('verticalMap', "600")
        self.configHorizontalMap = self.pluginPrefs.get('horizontalMap', "600")
        self.configZoomMap = self.pluginPrefs.get('ZoomMap', "15")
        self.datetimeFormat = self.pluginPrefs.get('datetimeFormat','%c')
        self.googleAPI = self.pluginPrefs.get('googleAPI','')
        self.deviceNeedsUpdated = ''
        self.openStore = self.pluginPrefs.get('openStore',False)
        # Convert old debugLevel scale to new scale if needed.
        # =============================================================
        if not isinstance(self.pluginPrefs['showDebugLevel'], int):
            if self.pluginPrefs['showDebugLevel'] == "High":
                self.pluginPrefs['showDebugLevel'] = 3
            elif self.pluginPrefs['showDebugLevel'] == "Medium":
                self.pluginPrefs['showDebugLevel'] = 2
            else:
                self.pluginPrefs['showDebugLevel'] = 1

        self.pluginIsInitializing = False
    ###
    ###  Update ghpu Routines.

    def checkForUpdates(self):

        updateavailable = self.updater.getLatestVersion()
        if updateavailable and self.openStore:
            indigo.server.log(u'FindFriendsMini: Update Checking.  Update is Available.  Taking you to plugin Store. ')
            self.sleep(2)
            self.pluginstoreUpdate()
        elif updateavailable and not self.openStore:
            self.errorLog(u'FindFriendsMini: Update Checking.  Update is Available.  Please check Store for details/download.')

    def updatePlugin(self):
        self.updater.update()

    def pluginstoreUpdate(self):
        iurl = 'http://www.indigodomo.com/pluginstore/139/'
        self.browserOpen(iurl)

    #####

    def __del__(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"__del__ method called.")

        indigo.PluginBase.__del__(self)

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"closedPrefsConfigUi() method called.")

        if userCancelled:
            self.debugLog(u"User prefs dialog cancelled.")

        if not userCancelled:
            self.debug = valuesDict.get('showDebugInfo', False)
            self.debugLevel = int(self.pluginPrefs.get('showDebugLevel', "1"))
            self.datetimeFormat = self.pluginPrefs.get('datetimeFormat', '%c')
            self.configVerticalMap = self.pluginPrefs.get('verticalMap', "600")
            self.configHorizontalMap = self.pluginPrefs.get('horizontalMap', "600")
            self.configZoomMap = self.pluginPrefs.get('ZoomMap', "15")
            self.datetimeFormat = self.pluginPrefs.get('datetimeFormat', '%c')
            self.googleAPI = self.pluginPrefs.get('googleAPI', '')
            self.openStore = self.pluginPrefs.get('openStore', False)
            self.updateFrequency = float(self.pluginPrefs.get('updateFrequency', "24")) * 60.0 * 60.0
            # If plugin config menu closed update the time for check.  Will apply after first change.
            self.configMenuTimeCheck = int(self.pluginPrefs.get('configMenuTimeCheck', "5"))
            self.debugLog(u"User prefs saved.")
            self.prefsUpdated = True

            if self.debug:
                indigo.server.log(u"Debugging on (Level: {0})".format(self.debugLevel))
            else:
                pass

            if int(self.pluginPrefs['showDebugLevel']) >= 3:
                self.debugLog(u"valuesDict: {0} ".format(valuesDict))

        return True

    def deviceStartComm(self, dev):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"deviceStartComm() method called.")
        self.debugLog(u'Starting FindFriendsMini device: '+unicode(dev.name)+' and dev.id:'+unicode(dev.id)+ ' and dev.type:'+unicode(dev.deviceTypeId))

        if dev.deviceTypeId=='FindFriendsGeofence':
            stateList = [
                {'key': 'friendsInRange', 'value': 0},
                {'key': 'lastArrivaltime', 'value': ''},
                {'key': 'lastDeptime', 'value': ''},
                {'key': 'lastArrivaltimestamp', 'value': ''},
                {'key': 'lastDeptimestamp', 'value': ''},
                {'key': 'minutessincelastArrival', 'value': 0},
                {'key': 'minutessincelastDep', 'value': 0},
                {'key': 'deviceIsOnline', 'value': False, 'uiValue':'Waiting'}]
            if self.debugLevel >= 2:
                self.debugLog(unicode(stateList))
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
                {'key': 'labels', 'value': ''},
                {'key': 'longitude', 'value': ''},
                {'key': 'horizontalAccuracy', 'value': ''},
                {'key': 'address', 'value': ''},
                {'key': 'latitude', 'value': ''}]
            if self.debugLevel >= 2:
                self.debugLog(unicode(stateList))
            dev.updateStatesOnServer(stateList)

        self.prefsUpdated = True
        # Update statelist in case any updates/changes
        dev.stateListOrDisplayStateIdChanged()
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Waiting")
        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

    def deviceStopComm(self, dev):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"deviceStopComm() method called.")
        self.debugLog(u"Stopping FindFriendsMini device: {0}".format(dev.name))
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Disabled")
        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

        # =============================================================

    def actionrefreshdata(self):
        if self.debugLevel >= 2:
            self.debugLog(u"actionrefreshdata() method called.")
        self.refreshData()
        self.sleep(5)
        self.checkGeofence()
        return

    def runConcurrentThread(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"ronConCurrentThread() method called.")

        #secondsbetweencheck = 60*self.configMenuTimeCheck

        if self.debugLevel >= 2:
            self.debugLog(u"secondsbetween Check Equal:"+unicode(60*self.configMenuTimeCheck))

        # Change to time based looping with second checking.  Allowing to update Geofences minutely and any config changes to be immediately registered
        while self.pluginIsShuttingDown == False:
        # Shutdown nicely

            if self.debugLevel >= 3:
                self.debugLog(u'ronConcurrrent loop: pluginshuttingdown=False Loop Running.')
            currenttimenow = time.time()
            nextloopdue = time.time() + 5  # currenttime plus 5 seconds when next loop is due.  Will need to reset with config changes.

            self.prefsUpdated = False
            self.sleep(0.5)
            updateGeofencedue = time.time() + 60 # Geofence update due in 65 seconds # should be reset below


            while self.prefsUpdated == False:
                if self.debugLevel >=3 and int(updateGeofencedue-time.time()) == 0:
                    self.debugLog(u'ronConcurrrent internal loop: self.prefsUpdated False: Next Update:'+unicode(int(time.time()-nextloopdue))+' and updateGeofenceDue:'+unicode(int(updateGeofencedue-time.time())))
                # Update Plugin Frequency Loop
                if self.updateFrequency > 0:
                    if time.time() > self.next_update_check:
                        try:
                            self.checkForUpdates()
                            self.next_update_check = time.time() + self.updateFrequency
                        except:
                            self.logger.debug(u'Error checking for update - ? No Internet connection.  Checking again in 24 hours')
                            self.next_update_check = self.next_update_check + 86400;
                # Update Loop Check.  Checks Devices and GeoFences.
                if time.time() > nextloopdue:
                    try:
                    #self.sleep()
                        if self.debugLevel >= 2:
                            self.debugLog(u'ronConcurrrent loop: Running Update:')
                        self.refreshData()
                        self.sleep(2)
                        self.checkGeofence()   #Check distances etc of GeoFences
                        nextloopdue = time.time() + int(60 * self.configMenuTimeCheck)
                        #reset Geofence time update as done above
                        updateGeofencedue = time.time() + 60
                        if self.debugLevel >= 2:
                            self.debugLog(u'ronConcurrrent loop: Next Update due (seconds):'+unicode(int(time.time()-nextloopdue)))
                    except:
                        self.debugLog(u'Error within RunConcurrentLoop Update cycle')
                        nextloopdue = time.time() + int(60 * self.configMenuTimeCheck)
                # Move to time for Geofences - so always in sync
                if time.time() > updateGeofencedue:
                    self.updateGeofencetime()
                    # add 60 seconds
                    updateGeofencedue = time.time() + 60

                self.sleep(1)

        if self.debugLevel >2:
            self.debugLog(u'Exiting self.pluginIsShuttingDown Loop.')


    def shutdown(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"Shutting down FindFriendsMini. shutdown() method called")
        self.pluginIsShuttingDown = True

    def startup(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"Starting FindFriendsMini. startup() method called.")
        self.updater = GitHubPluginUpdater(self)
        # Set appleAPI account as not verified on start of startup
        accountOK = False
        MAChome = os.path.expanduser("~") + "/"
        folderLocation = MAChome + "Documents/Indigo-iFindFriendMini/"
        if not os.path.exists(folderLocation):
            os.makedirs(folderLocation)

        appleAPIId = self.pluginPrefs.get('appleAPIid', '')

        if appleAPIId != '':
            if self.debugLevel >= 2:
                self.debugLog(u"AppleAPIID is not empty - logging in to appleAPI now.")
            username = self.pluginPrefs.get('appleId')
            password = self.pluginPrefs.get('applePwd')
            appleAPI = self.iAuthorise(username, password)

        if appleAPI[0] == 1:
            if self.debugLevel >= 2:
                self.debugLog(u"Login to icloud Failed.")

    def validateDeviceConfigUi(self, valuesDict, typeID, devId):
        """ Validate select device config menu settings. """

        # =============================================================
        # Device configuration validation Added DaveL17 17/12/19
        errorDict = indigo.Dict()
        self.debugLog(u"validateDeviceConfigUi() method called.")
        return True, valuesDict, errorDict

    def validatePrefsConfigUi(self, valuesDict):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"validatePrefsConfigUi() method called.")

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
                indigo.server.log("applePwd failed")
                return (False, valuesDict, errorDict)

        if 'applePwd' in valuesDict and 'appleId' in valuesDict:

            # Validate login
            iLogin = self.iAuthorise(valuesDict['appleId'], valuesDict['applePwd'])
            if not iLogin[0] == 0:
                # Failed login
                iFail = True
                errorDict["appleId"] = "Could not log in with that username/password combination"
                errorDict[
                    "showAlertText"] = "Login validation failed - check username & password or internet connection"
            else:
                # Get account details
                api = iLogin[1]
                    #indigo.server.log(u'Login Details**********:')
                    #indigo.server.log(unicode(api.friends.locations))
                # dev = indigo.devices[devId]
                accountOK = True
                valuesDict['appleAPIid'] = valuesDict['appleId']
                return True, valuesDict

            if iFail:
                indigo.server.log("Login to Apple Server Failed")
                return (False, valuesDict, errorDict)

        return True, valuesDict


    def getTheData(self):
        """ The getTheData() method is used to retrieve target data files. """
        if self.debugLevel >= 2:
            self.debugLog(u"gettheData() method called.  Not in use.  Refresh instead")
        return

    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataAction() method called.")
        self.refreshData()
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin devices.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshData() method called.")
        try:
            username = self.pluginPrefs.get('appleId', '')
            password = self.pluginPrefs.get('applePwd', '')
            appleAPIId = self.pluginPrefs.get('appleAPIid', '')

            if appleAPIId == '':
                self.indigo.log(u'Plugin Config Not setup.  Go to Plugin Config')
                return

            iLogin = self.iAuthorise(username, password)

            if iLogin[0] == 1:
                if self.debugLevel >= 2:
                    self.debugLog(u"Login to icloud Failed.")
                return

            appleAPI = iLogin[1]
            follower = iLogin[1].friends.locations
            if self.debugLevel >= 4:
                self.debugLog(unicode('Follower is Type: '+ unicode(type(follower))))
            if self.debugLevel >=4:
                self.debugLog(unicode('More debugging: Follower: '+unicode(iLogin[1].friends.locations)))
            if len(follower) == 0:
                indigo.server.log(u'No Followers Found for this Account.  Have you any friends?')
                if self.debugLevel >=4:
                    self.debugLog(u'Full Dump of AppleAPI data follows:')
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(unicode(iLogin[1].friends.data))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'Please PM developer this log.')
                    self.debugLog(u"{0:=^130}".format(""))
                return

            if follower is None:
                indigo.server.log(u'No Followers Found for this Account.  Have you any (enabled) friends?')
                if self.debugLevel >=4:
                    self.debugLog(u'Full Dump of AppleAPI data follows:')
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(unicode(iLogin[1].friends.data))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'Please PM developer this log.')
                    self.debugLog(u"{0:=^130}".format(""))
                return

            for dev in indigo.devices.itervalues("self.FindFriendsFriend"):
                # Check AppleID of Device
                if dev.enabled:
                    targetFriend = dev.pluginProps['targetFriend']
                    if self.debugLevel >= 4:
                        self.debugLog(u'targetFriend of Device equals:' + unicode(targetFriend))
                    for follow in follower:
                        if self.debugLevel >= 4:
                            self.debugLog (unicode(follow['id']))
                        if follow['id'] == targetFriend:
                            if self.debugLevel >=4:
                                self.debugLog(u'Found Target Friend in Data:  Updating Device:' + unicode(dev.name))
                                self.debugLog(unicode(follow))
                            # Update device with data from iFindFriends service
                            self.refreshDataForDev(dev, follow)
            return

        except Exception as e:
            indigo.server.log(u'Error within get Data.  ?Network connection or issue:  Error Given:'+unicode(e))
            indigo.server.log(u"{0:=^130}".format(""))
            indigo.server.log(u'Have you also logged on and setup new account on an Ios/iphone/ipad device?')
            indigo.server.log(u'You need to run and enable iOS FindmyFriends Application, you should see visible friends')
            indigo.server.log(u'This needs to be done, for FindmyFriends to work.  You cannot just create account.')
            indigo.server.log(u"{0:=^130}".format(""))
            return

    def updateGeofencetime(self):
        try:
            if self.debugLevel >2:
                self.debugLog('update GeoFences time called')

            for geoDevices in indigo.devices.itervalues('self.FindFriendsGeofence'):
                if geoDevices.enabled:
                    #localProps = geoDevices.pluginProps
                    lastArrivaltimestamp = float(geoDevices.states['lastArrivaltimestamp'])
                    lastDeptimestamp = float(geoDevices.states['lastDeptimestamp'])
                    if lastArrivaltimestamp > 0:
                        #indigo.server.log(unicode(lastArrivaltimestamp))
                        timesincearrival = int(t.time() - float(lastArrivaltimestamp)) / 60  # time in seconds /60
                        #indigo.server.log(unicode(timesincearrival))
                        geoDevices.updateStateOnServer('minutessincelastArrival', value=timesincearrival)
                    if lastDeptimestamp > 0:
                        timesincedep = int(t.time() - float(lastDeptimestamp)) / 60
                        geoDevices.updateStateOnServer('minutessincelastDep', value=timesincedep)

        except Exception as e:
            indigo.server.log(u'Error with updateGeoFence Time:' + unicode(e))
            pass

    def checkGeofence(self):
        try:
            if self.debugLevel >= 2:
                self.debugLog('Check GeoFences Called..')
            # need to start with GeofFence and then go through all devices
            # iDevName = dev.states['friendName']
            # Check GeoFences after devices
            for geoDevices in indigo.devices.itervalues('self.FindFriendsGeofence'):
                if geoDevices.enabled:
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

                    for dev in indigo.devices.itervalues("self.FindFriendsFriend"):
                        if dev.enabled:
                            if self.debugLevel >= 2:
                                self.debugLog('Geo Details on check:' + str(igeoName) + ' For Friend:' + unicode(dev.name))
                            iDevLatitude = float(dev.states['latitude'])
                            iDevLongitude = float(dev.states['longitude'])
                    # Now check the distance for each device
                    # Calculate the distance
                            if self.debugLevel >= 2:
                                self.debugLog('Point 1' + ' ' + str(igeoLat) + ',' + str(igeoLong) + ' Point 2 ' + str(iDevLatitude) + ',' + str(iDevLongitude))
                            iSeparation = iDistance(igeoLat, igeoLong, iDevLatitude, iDevLongitude)
                            if self.debugLevel > 2:
                                self.debugLog(unicode(iSeparation))
                            if not iSeparation[0]:
                                if self.debugLevel >= 2:
                                    self.debugLog(u'Problem with iSeparation.  Continue.')
                        # Problem with the distance so ignore and move on
                                continue
                            iSeparationABS = abs(iSeparation[1])
                    # if distance between to points smaller than range of GeoFence then is 'InRange' or within Geofence
                    # now need to count numbers.
                            if iSeparationABS <= igeoRangeDistance:
                                iDevGeoInRange = 'true'
                                igeoFriendsRange = igeoFriendsRange + 1
                            else:
                                iDevGeoInRange = 'false'
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
                    if igeoFriendsRange >0:
                        geoDevices.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                    try:
                        lastArrivaltimestamp = float(geoDevices.states['lastArrivaltimestamp'])
                        lastDeptimestamp = float(geoDevices.states['lastDeptimestamp'])
                        if lastArrivaltimestamp > 0:
                            #indigo.server.log(unicode(lastArrivaltimestamp))
                            timesincearrival = int(t.time()-float(lastArrivaltimestamp))/60  #time in seconds /60
                            #indigo.server.log(unicode(timesincearrival))
                            geoDevices.updateStateOnServer('minutessincelastArrival', value=timesincearrival)
                        if lastDeptimestamp >0:
                            timesincedep = int(t.time()-float(lastDeptimestamp))/60
                            geoDevices.updateStateOnServer('minutessincelastDep', value=timesincedep)
                    except Exception as e:
                        indigo.server.log(u'Error with Departure/Arrival Time Calculation:'+unicode(e))
                        pass
                    geoDevices.updateStateOnServer('deviceIsOnline', value=True, uiValue='Online')
        except Exception as e:
            indigo.server.log(u'Error within Check GeoFences: '+unicode(e))
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
            indigo.server.log(u'Default web browser did not open - check Mac set up', isError = True)
            indigo.server.log(u'or issues contacting the www.latlong.net site.  Is internet working?', isError=True)
        return

    def refreshDataForDev(self, dev, follow):
        """ Refreshes device data. """

        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDev() method called.")
        try:
            if self.debugLevel >= 4:
                self.debugLog(
                unicode('Now updating Data for : ' + unicode(dev.name) + ' with data received: ' + unicode(follow)))
#
#
# Manage Labels provided by icloud data set
#
#
            UseLabelforState = False
            # Deal with Label Dict either Dict or None
            labels = follow['location']['labels']
            if len(labels) > 0:
                label = labels[0]
            else:
                label = labels

            if self.debugLevel >=4:
                self.debugLog(unicode('Label:' + unicode(label) + ' and type is ' + unicode(type(label))))

            if isinstance(label, dict):
                if 'label' in label:
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
#   Create stateList ? need better checking that exists
#
            address =""
            if 'formattedAddressLines' in follow['location']['address']:
                address = ','.join(follow['location']['address']['formattedAddressLines'])
            elif 'address' in follow['location']:
                if 'streetAddress' in follow['location']['address']:
                    address = follow['location']['address']['streetAddress']
                if 'locality' in follow['location']['address']:
                    address = address + ' '+ follow['location']['address']['locality']

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
            ]
            if self.debugLevel >= 2:
                self.debugLog(unicode(stateList))
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
            self.godoMapping(str(follow['location']['latitude']),str(follow['location']['longitude']),dev)
            return

        except Exception as e:
            indigo.server.log(unicode('Exception in refreshDataforDev: ' + unicode(e)))
            indigo.server.log(unicode('Possibility missing some data from icloud:  Is your account setup with FindFriends enabled on iOS/Mobile device?'))
            dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            return

    def godoMapping(self, latitude, longitude, dev):

        if self.debugLevel >= 2:
            self.debugLog(u"godoMapping() method called.")
        try:
            MAChome = os.path.expanduser("~") + "/"
            folderLocation = MAChome + "Documents/Indigo-iFindFriendMini/"

            filename = dev.name.replace(' ','_')+'_Map.jpg'
            file = folderLocation +filename
            #Generate single device URL
            drawUrl = urlGenerate(self, latitude ,longitude , self.googleAPI, int(self.configHorizontalMap), int(self.configVerticalMap), int(self.configZoomMap), dev)
            if self.debugLevel >= 4:
                webbrowser.open_new(drawUrl)

            fileMap = "curl --output '" + file + "' --url '" + drawUrl + "'"
            os.system(fileMap)

            if self.debugLevel >= 2:
                self.debugLog('Saving Map...' + file)

            filename = 'All_device.jpg'
            file = folderLocation + filename
            # Generate URL for All Maps
            drawUrl = urlAllGenerate(self, self.googleAPI,  int(self.configHorizontalMap), int(self.configVerticalMap), int(self.configZoomMap))
            fileMap = "curl --output '" + file + "' --url '" + drawUrl + "'"
            os.system(fileMap)
            if self.debugLevel >= 2:
                self.debugLog('Saving Map...' + file)

            if self.debugLevel >= 4:
                webbrowser.open_new(drawUrl)
                self.debugLog(unicode(drawUrl))
            return

        except Exception as e:
            indigo.server.log(u'Exception within godoMapping: '+unicode(e))


    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected
        device based on a plugin action call.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDevAction() method called.")
        return True


    def toggleDebugEnabled(self):
        """ Toggle debug on/off. """

        if self.debugLevel >= 2:
            self.debugLog(u"toggleDebugEnabled() method called.")

        if not self.debug:
            self.debug = True
            self.pluginPrefs['showDebugInfo'] = True
            indigo.server.log(u"Debugging on.")
            self.debugLog(u"Debug level: {0}".format(self.debugLevel))

        else:
            self.debug = False
            self.debugLevel = 1
            self.pluginPrefs['showDebugInfo'] = False
            self.pluginPrefs['showDebugLevel'] = 1
            indigo.server.log(u"Debugging off.  Debug level: {0}".format(self.debugLevel))

    def myFriendDevices(self, filter=0, valuesDict=None, typeId="", targetId=0):

        ################################################
        # Internal - Lists the Friends linked to an account
        try:
            if self.debugLevel >= 2:
                self.debugLog(unicode(u'myFriendDevices Called...'))
            # try:
            # Create an array where each entry is a list - the first item is
            # the value attribute and last is the display string that will be shown
            # Devices filtered on the chosen account

            #indigo.server.log(unicode(valuesDict))
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
                if self.debugLevel >= 2:
                    self.debugLog(u"Login to icloud Failed.")
                iWait = 0, 'Login to icloud Failed'
                iFriendArray.append(iWait)
                return iFriendArray

            follower = iLogin[1].friends.data['followers']
            for fol in follower:
                # indigo.server.log(unicode(fol['id']))
                # indigo.server.log(unicode(fol['invitationFromEmail']))
                iOption2 = fol['id'], fol['invitationFromEmail']
                #indigo.server.log(unicode(iOption2))
                iFriendArray.append(iOption2)
            return iFriendArray

        except:
            indigo.server.log(u'Error within myFriendsDevices')
            return []

    def iAuthorise(self, iUsername, iPassword):
        ################################################
        # Logs in and authorises access to the Find my Phone API
        # Logs into the find my phone API and returns an error if it doesn't work correctly
        if self.debugLevel >= 2:
            self.debugLog('Attempting login...')
        # Logs into the API as required
        try:
            appleAPI = PyiCloudService(iUsername, iPassword)

            if self.debugLevel > 2:
                self.debugLog(u'Login successful...')

                if self.debugLevel >=4:
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'type AppleAPI result equals:')
                    self.debugLog(unicode(type(appleAPI)))
                    self.debugLog(u'AppleAPI.devices equals:')
                    self.debugLog(unicode(appleAPI.devices))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'AppleAPI.friends.details equals:')
                    self.debugLog(unicode(appleAPI.friends.details))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'AppleAPI.friends.locations equals:')
                    self.debugLog(unicode(appleAPI.friends.locations))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'Type of appleAPI.friends.locations equals:')
                    self.debugLog(unicode(type(appleAPI.friends.locations)))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'Type of appleAPI.friends.data')
                    self.debugLog(unicode(type(appleAPI.friends.data)))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'AppleAPI.friends.data equals')
                    self.debugLog(unicode(appleAPI.friends.data))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'appleAPI.friends.data[followers] equals:')
                    self.debugLog(unicode(appleAPI.friends.data['followers']))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))

                    follower = appleAPI.friends.data['followers']
                    self.debugLog(u'follower or appleAPI.friends.data[followers] equals:')
                    for fol in follower:
                        self.debugLog(u"{0:=^130}".format(""))
                        self.debugLog(u"{0:=^130}".format(""))
                        self.debugLog(u'Follower in follower: ID equals')
                        self.debugLog(unicode(fol['id']))
                        self.debugLog(u'email address from Id equals:')
                        self.debugLog(unicode(fol['invitationFromEmail']))

                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u'AppleAPI.friends.details equals:')
                    self.debugLog(unicode(appleAPI.friends.details))
                    self.debugLog(u"{0:=^130}".format(""))
                    self.debugLog(u"{0:=^130}".format(""))


            return 0, appleAPI

        except PyiCloudFailedLoginException:
            indigo.server.log(u'Login failed - Check username/password - has it changed recently.  2FA is not allowed/supported on this account',
                              type="FindFriendsMini Critical ", isError=True)
            return 1, 'NL'

        except PyiCloud2SARequiredError:
            indigo.server.log(u'Login failed - 2SA and 2FA Authenication are NOT supported.  Create new account without.',
                              type="FindFriendsMini Critical ", isError=True)
            return 1, 'NL'


        except Exception as e:
            indigo.server.log(u'Login Failed Error.  Is 2FA setup on this account? ' + unicode(e.message) + unicode(e.__dict__), type="iFindFriend Urgent ",
                              isError=True)
            return 1, 'NI'

def urlGenerate(self, latitude, longitude, mapAPIKey, iHorizontal, iVertical, iZoom, dev=0):
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
        if self.debugLevel >= 2:
            self.debugLog('** Device being mapped is:' + str(latitude) + ' ' + str(longitude))
        # Create Map url
        mapCentre = 'center=' + str(latitude) + "," + str(longitude)
        # Set zoom
        if iZoom < 0:
            iZoom = 0
        elif iZoom > 21:
            iZoom = 21
        mapZoom = 'zoom=' + str(iZoom)
        # Set size
        if iHorizontal > 640:
            iHorizontal = 640
        elif iHorizontal < 50:
            iHorizontal = 50

        if iVertical > 640:
            iVertical = 640
        elif iVertical < 50:
            iVertical = 50

        mapSize = 'size=' + str(iHorizontal) + 'x' + str(iVertical)
        mapFormat = 'format=jpg&maptype=hybrid'

        # Use a standard marker for a GeoFence Centre
        mapMarkerGeo = "markers=color:blue%7Csize:mid%7Clabel:G"
        mapMarkerPhone = "markers=icon:http://chart.apis.google.com/chart?chst=d_map_pin_icon%26chld=mobile%257CFF0000%7C" + str(
            latitude) + "," + str(longitude)
        mapGoogle = 'https://maps.googleapis.com/maps/api/staticmap?'

        if mapAPIKey == 'No Key':
            customURL = mapGoogle + mapCentre + '&' + mapZoom + '&' + mapSize + '&' + mapFormat + '&' + mapMarkerGeo + '&' + mapMarkerPhone
        else:
            customURL = mapGoogle + mapCentre + '&' + mapZoom + '&' + mapSize + '&' + mapFormat + '&' + mapMarkerGeo + '&' + mapMarkerPhone + '&key=' + mapAPIKey

        if self.debugLevel >= 2:
            self.debugLog(u'Map URL equals:'+unicode(customURL))
        return customURL

    except Exception as e:
        indigo.server.log(u'Mapping Exception/Error:'+unicode(e))


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

    global iDebug1, iDebug2, iDebug3, iDebug4, iDebug5, gIcon

    # Create geoFence list
    try:
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

        if mapAPIKey == 'No Key':
            customURL = mapGoogle+mapCentre+'&'+mapZoom+'&'+mapSize+'&'+mapFormat+'&'+mapMarkerGeo+'&'+mapMarkerPhone
        else:
            customURL = mapGoogle+mapCentre+'&'+mapZoom+'&'+mapSize+'&'+mapFormat+'&'+mapMarkerGeo+'&'+mapMarkerPhone+'&key='+mapAPIKey

        return customURL

    except Exception as e:
        indigo.server.log(u'urlAllGenerate'+unicode(e))
        return ''

def iDistance(lat1, long1, lat2, long2):

    ################################################
    # Once again thanks Mike and iFindStuff!
    # Calculates the 'As the crow flies' distance between
    # two points and returns value in metres

    global iDebug1, iDebug2, iDebug3, iDebug4, iDebug5, gUnits

    # First check if numbers are valid
    if lat1+long1 == 0.0 or lat2+long2 == 0.0:

        #  Zero default sent through
        indigo.server.log(u'No distance calculation possible as values are 0,0,0,0')
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
        indigo.server.log('Error within iDistance Calculation'+unicode(e))
        arc = 1
        pass

    # Remember to multiply arc by the radius of the earth
    # e.g. m to get actual distance in m

    mt_radius_of_earth = 6373000.0

    distance = arc * mt_radius_of_earth

    return True, distance