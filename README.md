**FindFriendsMini**

![](https://i0.wp.com/jimmymacsupport.com/wp-content/uploads/2014/12/Find-Friends-e1489951135224.png?w=512)

This plugin wouldn't be possible without Chameleons FindmyStuff indigo plugin which this is heavily based on. Thanks also go to DaveL for GhostXML and to pyicloud for the python icloud library. (Hopefully we see Mike/Chameleon back soon to update FindmyStuff - all the best -- Mike regardless)

This plugin is aimed at replacing (hopefully temporarily) findmyStuff, and overcomes the current and ongoing 2-Factor-Authenication issue that it seems all icloud library currently have.

As I understand it - The current state of play with 2FA is: 
*Main - PyiCloud, now Python 3 library*
Does not support 2FA it supports 2SA - which is different
 After some code changes we can get 2FA to work - however it times out after 2 hours and needs re-authentication. Clearly this isn't going to work.


This was initally envisioned as a quick update to iFindStuff enabling bypassing of non-functional 2FA. However updating iFindStuff began a rabbit hole I almost didn't escape out of!  And instead went down this path of writing a new plugin.

Hence this new, plugin: 

***FindFriendsMini***
It uses FindmyFriends icloud Service to enable tracking and mapping of enabled friends. It works somewhat differently to FindmyStuff and also has less information available. It does not use your 2FA/Main icloud account.

Enabling tracking and later mapping of device location It bypasses 2FA problems (which remain in the base python libraries currently) by not enabling it for the account used.

**Usage:**

Create an icloud Account (WITHOUT 2FA) ie. Your Indigo mac computer. (Some will have this already for imessage etc usage)
This account unfortunately needs to be also enabled on a iOS device (ie. ipad/iphone) Turn on FindmyFriends. Do no turn on 2-Factor-Authentication.

For those Friends/Family you need Indigo to track - send a friend request from this account/or other way around.

Once accepted those friends and the Indigo account will show up on your findmyfriends application in everyone device. If the Indigo account is there you should be good to go.
You can or your friends - delete this friend down the track or disable sharing of tracking  (probably slightly more honest/open way of tracking)
[Have yet to test this yet as to whether plugin handles well  -- It does -- have just checked -- will fail to update that friend (deviceLastUpdated time says old) and old location and mapping is still displayed]

*Prerequisites:*
**Need Indigo 7 only**

Install FindFriendMini Plugin from github/releases
https://github.com/Ghawken/IndigoPlugin-iFindFriendMini/releases

In FindFriendsMini Plugin Configuration - Create iCloud Account enter these details, confirm. (the plugin only supports on icloud account)
![](https://s17.postimg.org/s4ykmj34v/Plugin_Config.png)

Create New FindFriendsMini device - FindFriendDevice - Select the friend

For these friends the following custom states are Displayed: 

Address: Formatted with commas Altitude: 
batteryStatus: appears to be not reported
 deviceIsOnline 
deviceLastUpdated 
deviceTimeStamp 
horizontalAccuracy 
id 
labels 
latitude 
locationStatus: appears to be not reported 
locationTimeStamp: appears to be always 0 
longitude: 
status: 
timestamp appears to be also 0


![](https://s17.postimg.org/qd5lrmrhr/device_States.png)


**Mapping**


The plugin also creates a google [i]hybrid [/i]map for each Friend device and all_devices These are saved at: Users/accountname/Documents/Indigo-FindFriendsMini/

These are updated at the frequency set in the main config.


Whilst this doesn't recreate all the functionally of FindmyStuff -- it locates my set devices/enables address and mapping control page display which was my main usage.
To use these you ideally need a Google Maps API setup, as Mike describes well here:
http://forums.indigodomo.com/viewtopic.php?f=181&t=14734



Glenn