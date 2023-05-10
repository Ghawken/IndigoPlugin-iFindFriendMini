from __future__ import absolute_import
import json



class FindFriendsService(object):
    """
    The 'Find my Friends' iCloud service
    This connects to iCloud and returns friend data including the near-realtime
    latitude and longitude.
    """

    def __init__(self, service_root, session, params):
        self.session = session
        self.params = params
        self._service_root = service_root
        self._friend_endpoint = '%s/fmipservice/client/fmfWeb/initClient' % (
            self._service_root,
        )
        self._data = {}

    def refresh_data(self):
        """
        Fetches all data from Find my Friends endpoint
        """
        params = dict(self.params)

        fake_data = '{"dataContext":null,"serverContext":null,"clientContext":{"productType":"iphone6,1","appVersion":"1.0","contextApp":"com.icloud.web.fmf","userInactivityTimeInMS":537,"windowInFocus":false,"windowVisible":true,"mapkitAvailable":true,"tileServer":"Apple"}}'
        fake_data = '{"clientContext":{"appName":"FindMyiPhone","fmly":"True","clientTimestamp":"0","productType":"iphone14,2","appVersion":"5.0","buildVersion":"376","deviceUDID":"","osVersion":"14.0","inactiveTime":"1"}}'
        mock_payload = json.dumps(
            {
                "clientContext": {
                    "appVersion": "1.0",
                    "contextApp": "com.icloud.web.fmf",
                    "mapkitAvailable": True,
                    "productType": "fmfWeb",
                    "tileServer": "Apple",
                    "userInactivityTimeInMS": 537,
                    "windowInFocus": False,
                    "windowVisible": True,
                },
                "dataContext": None,
                "serverContext": None,
            }
        )
        req = self.session.post(self._friend_endpoint, data=mock_payload, params=params)
        self.response = req.json()
        return self.response

    @property
    def data(self):
        if not self._data:
            self._data = self.refresh_data()
        return self._data

    @property
    def locations(self):
        return "locations blank"

    @property
    def followers(self):
        return "followers blank"

    @property
    def friend_fences(self):
        return "fence blank"

    @property
    def my_fences(self):
        return "myFence Blank"

    @property
    def details(self):
        return "contactDetails Blank"

    @property
    def following(self):
        return "following Blank"