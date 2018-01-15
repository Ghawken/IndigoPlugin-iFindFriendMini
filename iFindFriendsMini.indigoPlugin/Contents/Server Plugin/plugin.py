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

import datetime
#from Queue import Queue
##import re
#import simplejson
#import subprocess
import sys
#import threading
import time as t

# Third-party imports
#import flatdict  # https://github.com/gmr/flatdict
import indigoPluginUpdateChecker

try:
    import indigo
except ImportError:
    pass

try:
    from pyicloud import PyiCloudService
    from pyicloud.exceptions import PyiCloudFailedLoginException

except:
    indigo.server.log("FATAL ERROR - Cannot find pyicloud - check with developer")
    indigo.server.log("Most probable error is pytz is not installed on your system. Read the forum for post on "
                      "Can't find pyicloud for more details and how to resolve."
                      "Alternatively - check the name of the plugin in the Plugins folder.  Is is iFindFriends.pluginIndigo"
                      "or iFindStuff(1).pluginIndigo?  Make sure that all iFindStuff files are deleted from Downloads"
                      "before downloading the latest versions")

# Now the HTTP and Compatibility libraries
try:
   # import six
    import requests

except:
    indigo.server.log("Note: requests.py must be installed for this plugin to operate.  See the forum")
    indigo.server.log(
        "Alternatively - check the name of the plugin in the Plugins folder.  Is is FindFirends.pluginIndigo"
        "or FindFriends(1).pluginIndigo?  Make sure that all iFindStuff files are deleted from Downloads"
        "before downloading the latest versions")

# Now the html mapping libraries - note that these have also been modified to allow custom icons
try:
    from pygmaps.pygmaps import maps
except:
    indigo.server.log("pygmaps.py error - No Map functionality availiable - contact Developer")

# Date and time libraries
import time

# Now install GeoCoder for reverse address lookup
# from pygeocoder import Geocoder, GeocoderError, GeocoderResult



try:
    import pydevd
except ImportError:
    pass

import webbrowser
import os



global accountOK
global appleAPI

# Custom imports
import iterateXML

__author__ = u"GlennNZ"
__build__ = u""
__copyright__ = u"There is no copyright for the code base."
__license__ = u"MIT"
__title__ = u"FindFriendsMini Plugin for Indigo Home Control"
__version__ = u"0.0.6"

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
        self.configMenuTimeCheck = int(self.pluginPrefs.get('configMenuTimeCheck', "15"))
        self.updater = indigoPluginUpdateChecker.updateChecker(self, "http://")
        self.updaterEmailsEnabled = self.pluginPrefs.get('updaterEmailsEnabled', False)

        self.configVerticalMap = self.pluginPrefs.get('verticalMap', "600")
        self.configHorizontalMap = self.pluginPrefs.get('horizontalMap', "600")
        self.configZoomMap = self.pluginPrefs.get('ZoomMap', "15")
        self.datetimeFormat = self.pluginPrefs.get('datetimeFormat','%c')
        self.googleAPI = self.pluginPrefs.get('googleAPI','')
        self.deviceNeedsUpdated = ''



        # Convert old debugLevel scale to new scale if needed.
        # =============================================================
        if not isinstance(self.pluginPrefs['showDebugLevel'], int):
            if self.pluginPrefs['showDebugLevel'] == "High":
                self.pluginPrefs['showDebugLevel'] = 3
            elif self.pluginPrefs['showDebugLevel'] == "Medium":
                self.pluginPrefs['showDebugLevel'] = 2
            else:
                self.pluginPrefs['showDebugLevel'] = 1

        # Adding support for remote debugging in PyCharm. Other remote
        # debugging facilities can be added, but only one can be run at a time.
        # try:
        #     pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
        # except:
        #     pass



        self.pluginIsInitializing = False

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
            self.debugLog(u"User prefs saved.")

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
        self.debugLog(u"Starting FindFriendsMini device: {0}".format(dev.name))
        dev.stateListOrDisplayStateIdChanged()
        dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Waiting")

    def deviceStopComm(self, dev):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"deviceStopComm() method called.")
        self.debugLog(u"Stopping FindFriendsMini device: {0}".format(dev.name))

        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Disabled")
        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

        # =============================================================

    def runConcurrentThread(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"indigoPluginUpdater() method called.")

        secondsbetweencheck = 60*self.configMenuTimeCheck

        if self.debugLevel >= 2:
            self.debugLog(u"secondsbetween Check Equal:"+unicode(secondsbetweencheck))

        while self.pluginIsShuttingDown == False:
            self.sleep(5)
            self.refreshData()
            self.sleep(secondsbetweencheck)

    def shutdown(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"Shutting down FindFriendsMini. shutdown() method called")

        self.pluginIsShuttingDown = True

    def startup(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"Starting FindFriendsMini. startup() method called.")

        #set locale here for current date/times



        # Set appleAPI account as not verified on start of startup
        accountOK = False
        MAChome = os.path.expanduser("~") + "/"
        folderLocation = MAChome + "Documents/Indigo-iFindFriendMini/"
        if not os.path.exists(folderLocation):
            os.makedirs(folderLocation)

        appleAPIId = self.pluginPrefs.get('appleAPIid', '')

        if appleAPIId != '':
            if self.debugLevel >= 2:
                self.debugLog(u"AppleAPIID is not empty - loging in to appleAPI now.")
            username = self.pluginPrefs.get('appleId')
            password = self.pluginPrefs.get('applePwd')
            appleAPI = self.iAuthorise(username, password)

        if appleAPI[0] == 1:
            if self.debugLevel >= 2:
                self.debugLog(u"Login to icloud Failed.")

        try:
            self.updater.checkVersionPoll()
        except Exception as sub_error:
            self.errorLog(u"Update checker error: {0}".format(sub_error))

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
                # iAccountNumber = str(dev.id)
                # dev.updateStateOnServer('accountActive', value="Active")
                # dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                # Devices in or added to Dictionary so return OK
                accountOK = True
                # indigo.server.log(u'appleAPIid:'+unicode(api['id']))
                valuesDict['appleAPIid'] = valuesDict['appleId']
                return True, valuesDict

            if iFail:
                indigo.server.log("Login to Apple Server Failed")
                return (False, valuesDict, errorDict)

        return True, valuesDict

    def checkVersionNow(self):
        """
        The checkVersionNow() method is called if user selects "Check For
        Plugin Updates..." Indigo menu item.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"checkVersionNow() method called.")

        try:
            self.updater.checkVersionNow()
        except Exception as sub_error:
            self.errorLog(u"Update checker error: {0}".format(sub_error))


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

            if self.debugLevel >= 2:
                self.debugLog(unicode(type(follower)))

            if len(follower) == 0:
                indigo.server.log(u'No Followers Found for this Account.  Have you any friends?')
                return

            for dev in indigo.devices.itervalues("self.FindFriendsFriend"):
                # Check AppleID of Device
                if dev.enabled:
                    targetFriend = dev.pluginProps['targetFriend']
                    if self.debugLevel >= 2:
                        self.debugLog(u'targetFriend of Device equals:' + unicode(targetFriend))
                    for follow in follower:
                        if self.debugLevel >= 2:
                            self.debugLog (unicode(follow['id']))
                        if follow['id'] == targetFriend:
                            if self.debugLevel >= 2:
                                self.debugLog(u'Found Target Friend in Data:  Updating Device:' + unicode(dev.name))
                                self.debugLog(unicode(follow))
                            self.refreshDataForDev(dev, follow)
            return

        except Exception as e:
            indigo.server.log(u'Error within get Data.  ?Network connection or issue.'+unicode(e))
            return


    def refreshDataForDev(self, dev, follow):
        """ Refreshes device data. """

        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDev() method called.")

        try:
            if self.debugLevel >= 2:
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

            if self.debugLevel >= 2:
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

            #update_time = t.strftime("%m/%d/%Y at %H:%M")
            # Change to Locale specific
            #update_time = t.strftime('%c')


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

            if self.debugLevel >= 2:
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

            if self.debugLevel >= 2:
                webbrowser.open_new(drawUrl)
                self.debugLog(unicode(drawUrl))

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
            indigo.server.log(u"Debugging off.")

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
                #indigo.server.log(u'appleAPI: Here we are 1.1 **************************:')
                # indigo.server.log(unicode(type(appleAPI)))
                # indigo.server.log(unicode(appleAPI.devices))
                # indigo.server.log(unicode(appleAPI.friends.details))
                #indigo.server.log(unicode(appleAPI.friends.locations))
                # indigo.server.log(unicode(type(appleAPI.friends.locations)))
                # indigo.server.log(unicode(type(appleAPI.friends.data)))
                #indigo.server.log(unicode(appleAPI.friends.data['followers']))
                # follower = appleAPI.friends.data['followers']
                # for fol in follower:
                #   indigo.server.log(unicode(fol['id']))
                #   indigo.server.log(unicode(fol['invitationFromEmail']))
                # indigo.server.log(unicode(appleAPI.friends.details))
            return 0, appleAPI

        except PyiCloudFailedLoginException as e:
            indigo.server.log(u'Login failed -:' + unicode(e.message), type="iFindFriends Critical ", isError=True)
            return 1, 'NL'

        except Exception as e:
            indigo.server.log(u'Error ...' + unicode(e.message) + unicode(e.__dict__), type="iFindFriend Urgent ",
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