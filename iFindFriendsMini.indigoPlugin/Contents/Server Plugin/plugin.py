#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
FindFriendsMini
Authors: See (repo)

Logons on to icloud account and access friends information for creation of indigo Devices

Enormously based on FindiStuff by Chameleon and GhostXML by DaveL17

"""

# Stock imports
import datetime
from Queue import Queue
import re
import simplejson
import subprocess
import sys
import threading
import time as t

# Third-party imports
import flatdict  # https://github.com/gmr/flatdict
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
    import six
    import requests

except:
    indigo.server.log("Note: requests.py and six.py must be installed for this plugin to operate.  See the forum")
    indigo.server.log(
        "Alternatively - check the name of the plugin in the Plugins folder.  Is is iFindFirends.pluginIndigo"
        "or iFindFriends(1).pluginIndigo?  Make sure that all iFindStuff files are deleted from Downloads"
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

global accountOK
global appleAPI

# Custom imports
import iterateXML

__author__ = u"GlennNZ"
__build__ = u""
__copyright__ = u"There is no copyright for the code base."
__license__ = u"MIT"
__title__ = u"FindFriendsMini Plugin for Indigo Home Control"
__version__ = u"0.0.1"

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
        self.prefServerTimeout = int(self.pluginPrefs.get('configMenuServerTimeout', "15"))
        self.updater = indigoPluginUpdateChecker.updateChecker(self, "http://")
        self.updaterEmailsEnabled = self.pluginPrefs.get('updaterEmailsEnabled', False)

        self.deviceNeedsUpdated = ''
        self.finalDict = {}
        self.jsonRawData = {}
        self.rawData = ''

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

        while self.pluginIsShuttingDown == False:
            self.sleep(5)
            self.refreshData()
            self.sleep(180)

    def shutdown(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"Shutting down FindFriendsMini. shutdown() method called")

        self.pluginIsShuttingDown = True

    def startup(self):
        """ docstring placeholder """

        if self.debugLevel >= 2:
            self.debugLog(u"Starting FindFriendsMini. startup() method called.")
        # Set appleAPI account as not verified on start of startup
        accountOK = False
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
                indigo.server.log(u'Login Details**********:')
                indigo.server.log(unicode(api.friends.locations))
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

    def killAllComms(self):
        """
        killAllComms() sets the enabled status of all plugin devices to false.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"killAllComms() method called.")

    def unkillAllComms(self):
        """
        unkillAllComms() sets the enabled status of all plugin devices to true.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"unkillAllComms() method called.")

    def fixErrorState(self, dev):
        """
        If the 'deviceLastUpdated' state is an empty string, populate the state
        with a valid timestamp.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"fixErrorState() method called.")
        return

    def getTheData(self):
        """ The getTheData() method is used to retrieve target data files. """
        if self.debugLevel >= 2:
            self.debugLog(u"gettheData() method called.  Not in use.  Refresh instead")

        return

    def cleanTheKeys(self, input_data):
        """
        Some dictionaries may have keys that contain problematic characters
        which Indigo doesn't like as state names. Let's get those characters
        out of there.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"cleanTheKeys() method called.")

        try:
            ###########################
            # Added by DaveL17 on 16/11/25.
            # Some characters need to be replaced with a valid replacement
            # value because simply deleting them could cause problems. Add
            # additional k/v pairs to chars_to_replace as needed.

            ###########################
            # ADDED BY GlennNZ 28.11.16
            # add true for True and false for False exchanges

            chars_to_replace = {'_ghostxml_': '_', '+': '_plus_', '-': '_minus_', 'true': 'True', 'false': 'False'}
            chars_to_replace = dict((re.escape(k), v) for k, v in chars_to_replace.iteritems())
            pattern = re.compile("|".join(chars_to_replace.keys()))

            for key in input_data.iterkeys():
                new_key = pattern.sub(lambda m: chars_to_replace[re.escape(m.group(0))], key)
                input_data[new_key] = input_data.pop(key)

            # Some characters can simply be eliminated. If something here
            # causes problems, remove the element from the set and add it to
            # the replacement dict above.
            chars_to_remove = {'/', '(', ')'}

            for key in input_data.iterkeys():
                new_key = ''.join([c for c in key if c not in chars_to_remove])
                input_data[new_key] = input_data.pop(key)

            ###########################
            # Added by DaveL17 on 16/11/28.
            # Indigo will not accept device state names that begin with a
            # number, so inspect them and prepend any with the string "No_" to
            # force them to something that Indigo will accept.
            temp_dict = {}

            for key in input_data.keys():
                if key[0].isdigit():
                    temp_dict[u'No_{0}'.format(key)] = input_data[key]
                else:
                    temp_dict[key] = input_data[key]

            input_data = temp_dict

            self.jsonRawData = input_data

            ###########################
            # ADDED BY GlennNZ 28.11.16
            # More debug
            if self.debugLevel >= 2:
                self.debugLog("cleanTheKeys result:")
                self.debugLog(self.jsonRawData)

        except Exception as sub_error:
            self.errorLog(u'Error cleaning dictionary keys: {0}'.format(sub_error))

    def parseTheJSON(self, dev, root):
        """
        The parseTheJSON() method contains the steps to convert the JSON file
        into a flat dict.

        http://github.com/gmr/flatdict
        class flatdict.FlatDict(value=None, delimiter=None, former_type=<type 'dict'>)
        """

        if self.debugLevel >= 2:
            self.debugLog(u"parseTheJSON() method called.")
        try:
            parsed_simplejson = simplejson.loads(root)

            if self.debugLevel >= 2:
                self.debugLog(u"Prior to FlatDict Running JSON")
                self.debugLog(parsed_simplejson)

            ###########################
            # ADDED BY GlennNZ 28.11.16
            # Check if list and then flatten to allow FlatDict to work in
            # theory!
            #
            # if List flattens once - with addition of No_ to the beginning
            # (Indigo appears to not allow DeviceNames to start with Numbers)
            # then flatDict runs - and appears to run correctly (as no longer
            # list - dict) if isinstance(list) then will flatten list down to
            # dict.

            if isinstance(parsed_simplejson, list):

                if self.debugLevel >= 2:
                    self.debugLog(u"List Detected - Flattening to Dict")

                # =============================================================
                # Added by DaveL17 17/12/13
                # Updates to Unicode.
                parsed_simplejson = dict((u"No_" + unicode(i), v) for (i, v) in enumerate(parsed_simplejson))
                # =============================================================

            if self.debugLevel >= 2:
                self.debugLog(u"After List Check, Before FlatDict Running JSON")

            self.jsonRawData = flatdict.FlatDict(parsed_simplejson, delimiter='_ghostxml_')

            if self.debugLevel >= 2:
                self.debugLog(self.jsonRawData)

            return self.jsonRawData

        except Exception as sub_error:
            self.errorLog(dev.name + ": " + unicode(sub_error))

    def parseStateValues(self, dev):
        """
        The parseStateValues() method walks through the dict and assigns the
        corresponding value to each device state.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"parseStateValues() method called.")

        self.debugLog(u"Writing device states:")

        sorted_list = sorted(self.finalDict.iterkeys())
        for key in sorted_list:
            try:
                if self.debugLevel >= 3:
                    self.debugLog(u"   {0} = {1}".format(key, self.finalDict[key]))
                dev.updateStateOnServer(unicode(key), value=unicode(self.finalDict[key]))

            except Exception as sub_error:
                self.errorLog(
                    u"Error parsing key/value pair: {0} = {1}. Reason: {2}".format(key, self.finalDict[key], sub_error))
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Error")

    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataAction() method called.")
        self.refreshData(self)
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin devices.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshData() method called.")
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
        indigo.server.log(unicode(type(follower)))

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
                    indigo.server.log(unicode(follow['id']))
                    if follow['id'] == targetFriend:
                        if self.debugLevel >= 2:
                            indigo.server.log(u'Found Target Friend in Data:  Updating Device:' + unicode(dev.name))
                            indigo.server.log(unicode(follow))
                        self.refreshDataForDev(dev, follow)
        return

    def refreshDataForDev(self, dev, follow):
        """ Refreshes device data. """

        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDev() method called.")

        try:
            indigo.server.log(
                unicode('Now updating Data for : ' + unicode(dev.name) + ' with data received: ' + unicode(follow)))
            UseLabelforState = False
            # Deal with Label Dict either Dict or None
            labels = follow['location']['labels']
            if len(labels) > 0:
                label = labels[0]
            else:
                label = labels

            if self.debugLevel >= 2:
                indigo.server.log(unicode('Label:' + unicode(label) + ' and type is ' + unicode(type(label))))

            if isinstance(label, dict):
                if 'label' in label:
                    labeltouse = label['label']
                    UseLabelforState = True
            elif isinstance(label, list):
                labeltouse = ','.join(follow['location']['labels'])
            elif label == None:
                labeltouse = 'nil'

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
                {'key': 'address', 'value': ','.join(follow['location']['address']['formattedAddressLines'])},
                {'key': 'latitude', 'value': follow['location']['latitude']},
            ]
            if self.debugLevel >= 2:
                indigo.server.log(unicode(stateList))
            dev.updateStatesOnServer(stateList)

            update_time = t.strftime("%m/%d/%Y at %H:%M")
            dev.updateStateOnServer('deviceLastUpdated', value=update_time)
            dev.updateStateOnServer('deviceTimestamp', value=t.time())

            if UseLabelforState:
                dev.updateStateOnServer('deviceIsOnline', value=True, uiValue=labeltouse)
            else:
                dev.updateStateOnServer('deviceIsOnline', value=True, uiValue=dev.states['address'])

            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

            #drawUrl = urlGenerate(self, str(follow['location']['latitude']), str(follow['location']['longitude']), '', 600, 600, 15, dev)
            drawUrl = urlAllGenerate(self, '',  600, 600, 15)
            indigo.server.log(unicode(drawUrl))

            webbrowser.open_new(drawUrl)

            return

        except Exception as e:
            indigo.server.log(unicode('Exception in refreshDataforDev: ' + unicode(e)))
            dev.updateStateOnServer('deviceIsOnline', value=False, uiValue='Offline')
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            return

        return

    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected
        device based on a plugin action call.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDevAction() method called.")

        return True

    def stopSleep(self, start_sleep):
        """
        The stopSleep() method accounts for changes to the user upload
        interval preference. The plugin checks every 2 seconds to see if the
        sleep interval should be updated.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"stopSleep() method called.")

        total_sleep = float(self.pluginPrefs.get('configMenuUploadInterval', 300))

        if t.time() - start_sleep > total_sleep:
            return True

        return False

    def stripNamespace(self, dev, root):
        """
        The stripNamespace() method strips any XML namespace values, and loads
        into self.rawData.
        """

        if self.debugLevel >= 2:
            self.debugLog(u"stripNamespace() method called.")

    def timeToUpdate(self, dev):
        """
        Returns True if the device is ready to be updated, else returns False.
        """

        # We don't make a log entry when this method is called because it's called every 2 seconds.

        # If device has a deviceTimestamp key and is enabled.
        if "deviceTimestamp" in dev.states.iterkeys() and dev.enabled:  # Added dev.enabled test - DaveL17 17/09/18

            # If the device timestamp is an empty string, set it to a valid value.
            if dev.states["deviceTimestamp"] == "":
                self.fixErrorState(dev)

            # If the refresh frequency is zero, the device is a manual only refresh.
            if int(dev.pluginProps.get("refreshFreq", 300)) == 0:
                self.debugLog(
                    u"    Refresh frequency: {0} (Manual refresh only)".format(dev.pluginProps["refreshFreq"]))
                return False

            # If the refresh frequency is not zero, test to see if the device is ready for a refresh.
            else:
                t_since_upd = int(t.time() - float(dev.states["deviceTimestamp"]))

                # If it's time for the device to be updated.
                if int(t_since_upd) > int(dev.pluginProps.get("refreshFreq", 300)):
                    self.debugLog(
                        u"Time since update ({0}) is greater than configured frequency ({1})".format(t_since_upd,
                                                                                                     dev.pluginProps[
                                                                                                         "refreshFreq"]))
                    return True

                # If it's not time for the device to be updated.
                return False

        # If the device does not have a timestamp key and/or is disabled.
        else:
            return False

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
            self.pluginPrefs['showDebugInfo'] = False
            indigo.server.log(u"Debugging off.")

    def myFriendDevices(self, filter=0, valuesDict=None, typeId="", targetId=0):

        ################################################
        # Internal - Lists the Friends linked to an account
        try:

            indigo.server.log(unicode(u'myFriendDevices Called...'))
            # try:
            # Create an array where each entry is a list - the first item is
            # the value attribute and last is the display string that will be shown
            # Devices filtered on the chosen account

            indigo.server.log(unicode(valuesDict))
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
                indigo.server.log(unicode(iOption2))
                iFriendArray.append(iOption2)
            return iFriendArray

        except:
            indigo.server.log(u'Error within myFriendsDevices')
            return []

    def iAuthorise(self, iUsername, iPassword):
        ################################################
        # Logs in and authorises access to the Find my Phone API
        # Logs into the find my phone API and returns an error if it doesn't work correctly
        indigo.server.log(u'Attempting login...')

        # Logs into the API as required
        try:
            appleAPI = PyiCloudService(iUsername, iPassword)

            if self.debugLevel > 2:
                indigo.server.log(u'Login successful...')
                indigo.server.log(u'appleAPI: Here we are 1.1 **************************:')
                # indigo.server.log(unicode(type(appleAPI)))
                # indigo.server.log(unicode(appleAPI.devices))
                # indigo.server.log(unicode(appleAPI.friends.details))
                indigo.server.log(unicode(appleAPI.friends.locations))
                # indigo.server.log(unicode(type(appleAPI.friends.locations)))
                # indigo.server.log(unicode(type(appleAPI.friends.data)))
                indigo.server.log(unicode(appleAPI.friends.data['followers']))
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


def urlGenerate(self, latitude, longitude, mapAPIKey='No Key', iHorizontal=600, iVertical=300, iZoom=15, dev=0):
    ################################################
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
            indigo.server.log('** Device being mapped is:' + str(latitude) + ' ' + str(longitude))
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
        mapFormat = 'format=jpg'

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
            indigo.server.log(u'Map URL equals:'+unicode(customURL))
        return customURL

    except Exception as e:
        indigo.server.log(u'Mapping Exception/Error:'+unicode(e))


def urlAllGenerate(self, mapAPIKey='No Key', iHorizontal=640, iVertical=640, iZoom=15):

    ################################################
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
        mapFormat='format=jpg'

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