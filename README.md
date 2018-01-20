***FindFriendsMini***

![](https://i0.wp.com/jimmymacsupport.com/wp-content/uploads/2014/12/Find-Friends-e1489951135224.png?w=512)

*Background*
This plugin wouldn't be possible without Chameleons FindmyStuff indigo plugin which this is heavily based on. Thanks also go to DaveL for GhostXML and to pyicloud for the python icloud library. (Hopefully we see Mike/Chameleon back soon to update FindmyStuff - all the best Mike, regardless)

This plugin is aimed at replacing (hopefully temporarily) findmyStuff, and overcomes the current and ongoing 2-Factor-Authenication issue that it seems all icloud libraries currently have.

As I understand it - The current state of play with 2FA is: 
*Main - PyiCloud, now Python 3 library*
Does not support 2FA,  it supports 2SA - which is different.
 After some code changes we can get 2FA to work - however it times out after 2 hours and needs re-authentication a new code. Clearly this isn't going to work.

This was initally envisioned as a quick update to iFindStuff enabling bypassing of non-functional 2FA. However updating iFindStuff began a rabbit hole I almost didn't escape out of!  And instead went down this path of writing a new plugin.

Hence this new, plugin: 

***FindFriendsMini***
It uses FindmyFriends icloud Service to enable tracking and mapping of enabled friends. It works somewhat differently to FindmyStuff and also has less information available. It does not use your 2FA/Main icloud account.   So this main account remains 'save' and you do not need to share details of this main account with the plugin.

The plugin allow location tracking and mapping of device/friend locations.   It bypasses 2FA problems (which remain in the base python libraries currently) by not enabling it for the account used.  It also allows GeoFences to be created and then lets you know how many are within and for how long.

**Setup:**

Create an potentially new icloud Account (WITHOUT 2FA turned on) 
ie. Your Indigo mac computer. (Some will have this already for imessage etc usage)
**Important:**
This account unfortunately needs to be also enabled and logged on to a iOS device (ie. ipad/iphone).  (at least once)
Turn on FindmyFriends on this iOS device.
Do not turn on 2-Factor-Authentication for this account.

For those Friends/Family you need Indigo to track - send a friend request from this new account/or other way around.

Once accepted those friends and your new icloud/ndigo account will show up on your findmyfriends application in everyone’s device. If the Indigo account is in the findmyfriends account  you should be good to go.

You can or your friends - can disable sharing of tracking with this indigo account (which is probably slightly more honest/open way of tracking)
[If tracking is disabled by a Friend the plugin will fail to update that friend (deviceLastUpdated time says old) and old location and mapping is still displayed]

It’s actually pretty simple:

*For example*

Create new iCloud account indigo@icloud.com
**Sign in on IPad/Iphone **
**Sign in to FindmyFriends app on iphone/ipad**
Send a friend request to those you want to share location with.
E.g friend1@icloud.com, friend2@icloud, friend3@icloud.com
If and when they accept you request they will show up in Findmyfriends app.

Install the plugin from Plugin Store:
Setup your indigo@icloud.com account details in plugin config.
Add new FindFriendsMini Device - selecting which friend.
E.g friend1@icloud.com
Create a new FindFriendsMini Device for each friend you wish indigo to locate.
The plugin will populate the custom states and location for each of these devices and create a hybrid google map for all the friends, and one for each friend individually.

*Prerequisites:*
**Indigo 7 only**

Install Plugin from Plugin Store:
[url]http://www.indigodomo.com/pluginstore/139/[/url]

In FindFriendsMini Plugin Configuration (Most of the settings are here)
Enter iCloud Account enter these details, confirm. (the plugin only supports one main icloud account)

![](https://kek.gg/i/6BNfQv.png)

Plugin Config Options:
**Account Details:**
Apple Account ID:  Your new icloud account, setup on ipad/iphone without 2-factor-authentication enabled.
Apple Account Passport:
Minutes between rechecking status of devices and Geofences:  5 minutes default
**Mapping:**
Vertical size of Map max allowed by Google is 640, in pixels
Horizontal size of Map max allowed by Google is 640, in pixels
Zoom Size of Map 0-20
Google API:  Need this for maps downloads.  Create free API as below
[url]http://forums.indigodomo.com/viewtopic.php?f=181&t=14734[/url]
**Date/Time Format**
Allows custom lastUpdate date/times.  In pythons strftime format.
            eg  %c  == Mon Jan 15 16:50:59 2018
            eg.  %b %d %Y %H:%M:%S == Feb 18 2009 00:03:38
            eg. %a %d %b %I:%M %p == Mon 15 Jan 4:57 PM
More examples here:
[url]http://strftime.org/[/url]
**Update Frequency**
Hours inbetween update checking.
Checkbox to open Plugin Store in default Webbrowser if update at time of check.
**Debugging**
Turn On/Off
Debug Level 1-3
& 4 which will open generated maps and url within browser.


*Create New FindFriendsMini device* 

FindFriendDevice - Select the friend from the pull down box
Give it a Unique Name
Rename the Indigo Device as you see fit.
![](https://s17.postimg.org/pep8ov15r/Find_Friends_Device.png)

For these friends the following custom states are Displayed: 
(some of which are currently not reported at least not for me)
(Interestingly some of these unreported fields do get reported in you have the FindmyFriends app open at the time of the check - altitude for example and potentially others I haven't noticed)


- Address: Formatted with commas
- Altitude:
- batteryStatus: appears to be not reported
- deviceIsOnline
- deviceLastUpdated
- deviceTimeStamp
- horizontalAccuracy
- id
- labels
- latitude
- locationStatus: appears to be not reported
- locationTimeStamp: appears to be always 0
- longitude:
- status:
- timestamp: appears to be also 0


![](https://s17.postimg.org/qd5lrmrhr/device_States.png)


***Action Group***

There is a single Device action group which immediately refreshes all friend devices and GeoFences (the data is all received together)

![](https://s17.postimg.org/4f94xx4sf/Action_Group.png)

**PluginConfig Menu Options**.

![](https://kek.gg/i/6MDT_D.png)

Check for Updates:  Checks github for updates and depending on config options will open Plugin Store
Open Plugin Store:  Opens Web Browser and takes you to Plugin Store Page
Refresh Data Now:  Updates all Friends/Geofences immediately


**Mapping**


The plugin also creates a google [i]hybrid [/i]map for each Friend device and a seperate all_devices map.  These are saved at: Users/accountname/Documents/Indigo-FindFriendsMini/

These are updated at the frequency set in the main config.

eg.
![](https://kek.gg/i/7s9DXk.png)



**Geofences**

Added GeoFence Devices:
Create new IndigoPlugin Device from within Indigo.
Selected Type of FindFriendsMini and Device FindFriends GeoFence as in here:
![](https://kek.gg/i/5GDzSW.png)

Edit Device Settings:

![](https://kek.gg/i/5WQmDH.png)

Name/Name
Latitude/Longitude
Range:  Circle of Geofence currently in Metres (sorry!)  [1m = 3.28 feet]

GeoFence Device States:
![](https://kek.gg/i/4vtkPh.png)

These stats are updated with Devices at same frequency (defaults to 5 minutes)
Stats of use:
- friendsinRange = number of friends within the Geofence.  Device is Green if more than 1 within, grey if noone
- lastArrivalTime = date/time in configured format of Last arrival
- lastDeptime = date/time in configured format of last Departure
- minutessincelastArrival  - minutes since this event.  Updated at same frequency of devices
- minutessincelastDep -

Allows triggering on state:
eg.  **if >20 minutes since someone left and 0 friend within Geofence - do something.**

![](https://kek.gg/i/6kjnLQ.png)

With Condition of:

![](https://kek.gg/i/6kjnLQ.png)

Then -->Action of your choice:


--------------------------------------------------------------------------------------------------------
Changelog:

Latest Version:
**0.1.4**
- Delete unused code/node - much smaller now!
- Tidy up uiValue/Values for Geofences
- Add Menu to check PluginStore
- Change Update code to use PluginStore (seems some changes coming to PluginStore - so best to use I suspect
- Change Plugin Config Menus.
- Add option to change update checking time/and enable automatic opening of PluginStore
- Some more logging advice for not setup correctly issues.
- Add icon.png for PluginStore

---------------------------------------------------------------------------------------------------------------------------------------------------------------------

Whilst this doesn't recreate all the functionally of FindmyStuff -- it locates my set devices/enables address display and mapping control page display which was my main usage, and now GeoFences for actions.

To use these you ideally need a Google Maps API setup, as Mike describes well here:  (depending on frequency of map refreshing)
http://forums.indigodomo.com/viewtopic.php?f=181&t=14734




Glenn