__author__ = 'Michael'
###############################################################################################
# Module is designed to provide location finding functionality for indigo using the
# Apple - Find my iPhone API
#
# Functions are:
#   Ability to locate and set up iXXXX devices
#   Ability to identify location and distance to trigger point
#   Ability to identify set a distance range for a trigger point
#
# This is designed to work independently of indigo initially as a proof of concept
#
#  Version 0.1
###############################################################################################

import sys
from pyicloud import PyiCloudService
import six
import time



# Set up the API
iCloudAPIStatus=[]
iCloudAPILocation = []

# Status first
iCloudAPIStatus.append('deviceDisplayName')
iCloudAPIStatus.append('deviceStatus')
iCloudAPIStatus.append('batteryLevel')
iCloudAPIStatus.append('name')
iCloudAPIStatus.append('deviceModel')
iCloudAPIStatus.append('locationEnabled')
iCloudAPIStatus.append('isLocating')

allStatusFields = []
for lines in range(len(iCloudAPIStatus)):
    allStatusFields.append(iCloudAPIStatus[lines])

# Now Location
iCloudAPILocation.append('timeStamp')
iCloudAPILocation.append('positionType')
iCloudAPILocation.append('horizontalAccuracy')
iCloudAPILocation.append('longitude')
iCloudAPILocation.append('latitude')
iCloudAPILocation.append('isOld')
iCloudAPILocation.append('isInaccurate')

allLocationFields = []
for lines in range(len(iCloudAPILocation)):
    allLocationFields.append(iCloudAPILocation[lines])

# Set up login
appleId = 'mike_hesketh@hotmail.com'
applePwd = 'caTs_178'

api = PyiCloudService(appleId, applePwd)
iDevices = api.devices
iDev = {}
for iDeviceId in range(len(iDevices.keys())):
    iStatusFields = []
    iStatus = iDevices[iDeviceId].status(allStatusFields)
    iLocation = iDevices[iDeviceId].location()

    if iStatus != None:
        for iAPIStat in iCloudAPIStatus:
            iStatusFields.append(iStatus[iAPIStat])
    else:
        iStatusFields.append('** No Status Information Found **')

    if iLocation != None:
        for iAPILoc in iCloudAPILocation:
            iStatusFields.append(iLocation[iAPILoc])
    else:
        iStatusFields.append('** No Location Data Found **')
    iDev['Apple '+str(iDeviceId)] = iStatusFields

iPhones = []
iTablets = []

for iDeviceId in range(0,len(iDevices.keys())):
    if iDev['Apple '+str(iDeviceId)][0].find('Phone') != -1:
        iPhones.append(str(iDev['Apple '+str(iDeviceId)]))
    elif iDev['Apple '+str(iDeviceId)][0].find('Pad') != -1:
        iTablets.append(str(iDev['Apple '+str(iDeviceId)]))

# Convert the data held and place in an array
iInformation = []

# iPhones first
if len(iPhones)>0:
    for iPhoneDevices in range(len(iPhones)):
        iTempData = ''
        iDevData = eval(iPhones[iPhoneDevices])
        for iData in range(len(iDevData)):
            if iData == 2: # Battery Level
                iTempData = iTempData+'\t'+str(int(iDevData[2]*100))+'%'
            elif iData == 7: # Time Stamp in ms
                iTime = time.asctime(time.localtime(int(iDevData[7]/1000)))
                iTempData = iTempData+'\t'+iTime
            else:
                try:
                    iTempData = iTempData+'\t'+str(iDevData[iData])
                except:
                    iTempData = iTempData+'\t'+iDevData[iData]

        # Store the result
        iInformation.append(iTempData)

if len(iTablets)>0:
    for iTabletDevices in range(len(iTablets)):
        iTempData = ''
        iDevData = eval(iTablets[iTabletDevices])
        for iData in range(len(iDevData)):
            if iData == 2: # Battery Level
                iTempData = iTempData+'\t'+str(iDevData[2]*100)+'%'
            elif iData == 7: # Time Stamp in ms
                iTime = time.asctime(time.localtime(int(iDevData[7]/1000)))
                iTempData = iTempData+'\t'+iTime
            else:
                try:
                    iTempData = iTempData+'\t'+str(iDevData[iData])
                except:
                    iTempData = iTempData+'\t'+iDevData[iData]

        # Store the result
        iInformation.append(iTempData)

# Print the data
print '*** iDevice information **'
print '=========================='+'\n'
for deviceNumber in range(len(iInformation)):
    print iInformation[deviceNumber]
