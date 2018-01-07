#FindFriendsMini

This plugin wouldn't be possible without Chameleon FindmyStuff indigo plugin which this is based on.  Thanks also go to DaveL for GhostXML and to pyicloud for the python icloud library.

This plugin is aimed at replacing (hopefully temporarily) findmyStuff, and overcomes the current and ongoing 2-Factor-Authenication issue that it seems all icloud library currently have.

As I understand it - The current state of play with 2FA is:
Main - PyiCloud Python 3 library
Does not support 2FA it supports 2SA - which is different
After some code changes we can get 2FA to work - however it times out after 2 hours and needs re-authenication.
Clearly this isn't going to work.


This was initally envisioned as a update to iFindStuff enabling bypassing of non-functional 2FA.
However updating iFindStuff began a rabbit hole I almost didn't escape out of!

Hence this new, plugin:
Uses FindmyFriends icloud Service to enable tracking and mapping of enabled friends.
It works somewhat differently to FindmyStuff and also has less information available.
It does not use your 2FA/Main icloud account.

Enabling tracking and later mapping of device location
It bypasses 2FA problems (which remain in the base python libraries currently) by not enabling it for the account used.

Usage:

Create an icloud Account (WITHOUT 2FA)  ie.  Your Indigo mac computer.
(Some will have this already for imessage etc usage)

This account unfortunately needs to be also enabled on a iOS device (ie. ipad/iphone) Turn on FindmyFriends.
Do no turn on 2-Factor-Authenication.

For those Friends/Family you need Indigo to track - send a friend request from this account/or other way around.

Once accepted those friends and the Indigo account will show up on your findmyfriends application.  If the Indigo account is there you should be good to go.

Install FindFriendMini Plugin from github/releases

In FindFriendsMini Plugin Configuration - Create iCloud Account enter these details, confirm.
(the plugin only supports on icloud account)

Create New FindFriendsMini device - FindFriendDevice - Select the friend

For these friends the following information is Displayed:
Address:  Formatted with commas
Altitude:
batteryStatus:  appears to be not reported
deviceIsOnline
deviceLastUpdated
deviceTimeStamp
horizontalAccuracy
id
labels
latitude
locationStatus:  appears to be not reported
locationTimeStamp:  appears to be always 0
longitude:
status:
timestamp appears to be also 0

Mapping

The plugin also creates a google hybrid map for each Friend device and all_devices
These are saved at:
Users/accountname/Documents/Indigo-FindFriendsMini/

These are updated at the frequency set in the main config.

