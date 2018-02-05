import uuid
import hashlib
import json
import logging
import pickle
import requests
import sys
import tempfile
import os
from re import match
import copy

from pyicloud.exceptions import (
    PyiCloudFailedLoginException,
    PyiCloudAPIResponseError,
    PyiCloud2SARequiredError,
    PyiCloudServiceNotActivatedErrror
)

from pyicloud.services import (
    #FindMyiPhoneServiceManager,
    FindFriendsService
    #CalendarService,
    #UbiquityService,
   # ContactsService
)


logger = logging.getLogger(__name__)


class PyiCloudService(object):
    """
    A base authentication class for the iCloud service. Handles the
    validation and authentication required to access iCloud services.

    Usage:
        from pyicloud import PyiCloudService
        pyicloud = PyiCloudService('username@apple.com', 'password')
        pyicloud.iphone.location()
    """
    def __init__(self, apple_id, password, cookie_directory=None):
        self.discovery = None
        self.logger = logging.getLogger('Plugin.PyiCloud')
        self.client_id = str(uuid.uuid1()).upper()
        self.user = {'apple_id': apple_id, 'password': password}

        #self.logger.debug(u'------------------------  self.user equals'+unicode(self.user))

        self._home_endpoint = 'https://www.icloud.com'
        self._setup_endpoint = 'https://setup.icloud.com/setup/ws/1'
        self._push_endpoint = 'https://p12-pushws.icloud.com'

        self._base_login_url = '%s/login' % self._setup_endpoint
        self._base_validate_url = '%s/validate' % self._setup_endpoint
        #self._base_system_url = '%s/system/version.json' % self._home_endpoint
        #self._base_webauth_url = '%s/refreshWebAuth' % self._push_endpoint

        self._cookie_directory = 'cookies'

        self.data ={}

        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'Origin': self._home_endpoint,
            'Referer': '%s/' % self._home_endpoint,
            'User-Agent': 'Opera/9.52 (X11; Linux i686; U; en)'
        })

        self.params = {}

        self.authenticate()

    def refresh_validate(self):
        """
        Queries the /validate endpoint and fetches two key values we need:
        1. "dsInfo" is a nested object which contains the "dsid" integer.
            This object doesn't exist until *after* the login has taken place,
            the first request will compain about a X-APPLE-WEBAUTH-TOKEN cookie
        2. "instance" is an int which is used to build the "id" query string.
            This is, pseudo: sha1(email + "instance") to uppercase.
        """
        req = self.session.get(self._base_validate_url, params=self.params)
        resp = req.json()
        if 'dsInfo' in resp:
            dsid = resp['dsInfo']['dsid']
            self.params.update({'dsid': dsid})
        instance = resp.get(
            'instance',
            uuid.uuid4().hex.encode('utf-8')
        )
        sha = hashlib.sha1(
            self.user.get('apple_id').encode('utf-8') + instance
        )
        self.params.update({'id': sha.hexdigest().upper()})

        clientId = str(uuid.uuid1()).upper()
        self.params.update({
            'clientBuildNumber': '14E45',
            'clientId': clientId,
        })

    def authenticate(self):
        """
        Handles the full authentication steps, validating,
        authenticating and then validating again.
        """
        self.refresh_validate()
        '''
        # Check if cookies directory exists
        if not os.path.exists(self._cookie_directory):
            # If not, create it
            os.mkdir(self._cookie_directory)

        cookie = self._get_cookie()
        if cookie:
            self.session.cookies = cookie
        '''
        # Check if cookies directory exists
        if not os.path.exists(self._cookie_directory):
            # If not, create it
            os.mkdir(self._cookie_directory)

        # Set path for cookie file
        cookiefile = self.user.get('apple_id')
        cookiefile = os.path.join(self._cookie_directory, ''.join([c for c in cookiefile if match(r'\w', c)]))

        # Check if cookie file already exists
        if os.path.isfile(cookiefile):
            # Get cookie data from file
            with open(cookiefile, 'rb') as f:
                webKBCookie = pickle.load(f)
            self.session.cookies = requests.utils.cookiejar_from_dict(webKBCookie)
        else:
            webKBCookie = None

        data = dict(self.user)
        data.update({'id': self.params['id'], 'extended_login': False})

        try:
            req = self.session.post(
                self._base_login_url,
                params=self.params,
                data=json.dumps(data)
            )



        except PyiCloudAPIResponseError as error:
            msg ='API Response Error.  Invalid email/passwoprd'
            #msg = req.json()
            self.logger.exception(u'PyiCloud Login error:')
            raise PyiCloudFailedLoginException(msg, error)

        #content_type = req.headers.get('Content-Type', '').split(';')[0]
        #json_mimetypes = ['application/json', 'text/json']

        if not req.ok:
            msg = 'Invalid email/password combination.'
#           msg = req.json()
            self.logger.debug(u'PyiCloud Req Not OK:  msg:'+unicode(req))
            raise PyiCloudFailedLoginException(msg)


        # Glenn added dump and save the Whole Cookie File
        # with open(cookiefile, 'wb') as f:
        #   pickle.dump(req.cookies,f)

        # Pull X-APPLE-WEB-KB cookie from cookies

        NewWebKBCookie = next(({key:val} for key, val in req.cookies.items() if 'X-APPLE-WEB-KB' in key), None)

        # GlennNZ Additional - if WebCookie Empty check for underscoring formatting which Apples appears to have changed to !
        # NOTE Change from APPLE to X underscore APPLE  -- previous X Dash Apple etc.
        if not NewWebKBCookie:
            NewWebKBCookie = next(({key:val} for key, val in req.cookies.items() if 'X_APPLE_WEB_KB' in key), None)

        if NewWebKBCookie and NewWebKBCookie != webKBCookie:
            # Save the cookie in a pickle file
            with open(cookiefile, 'wb') as f:
                pickle.dump(NewWebKBCookie, f)

        self.refresh_validate()

        self.discovery = req.json()
        self.data = req.json()
        self.webservices = self.discovery['webservices']

    '''
    def _get_cookie_path(self):
        # Set path for cookie file
        return os.path.join(
            self._cookie_directory,
            ''.join([c for c in self.user.get('apple_id') if match(r'\w', c)])
        )

    def _get_cookie(self):
        if hasattr(self, '_cookies'):
            return self._cookies

        cookiefile = self._get_cookie_path()

        # Check if cookie file already exists
        try:
            # Get cookie data from file
            with open(cookiefile, 'rb') as f:
                return pickle.load(f)
        except IOError:
            # This just means that the file doesn't exist; that's OK!
            pass
        except Exception as e:
            logger.exception(
                "Unexpected error occurred while loading cookies: %s" % (e, )
            )

        return None

    def _update_cookie(self, request):
        cookiefile = self._get_cookie_path()

        # Save the cookie in a pickle file
        with open(cookiefile, 'wb') as f:
            pickle.dump(request.cookies, f)

        self._cookies = request.cookies
    '''
    @property
    def requires_2sa(self):
        """ Returns True if two-step authentication is required."""
        return self.data.get('hsaChallengeRequired', False) \
            and self.data['dsInfo'].get('hsaVersion', 0) >= 1
        # FIXME: Implement 2FA for hsaVersion == 2


    @property
    def devices(self):
        """ Return all Friends."""
        service_root = self.webservices['findme']['url']
        return FindMyiPhoneServiceManager(
            service_root,
            self.session,
            self.params
        )

    @property
    def iphone(self):
        return self.devices[0]

    @property
    def files(self):
        if not hasattr(self, '_files'):
            service_root = self.webservices['ubiquity']['url']
            self._files = UbiquityService(
                service_root,
                self.session,
                self.params
            )
        return self._files

    @property
    def friends(self):
        service_root = self.webservices['fmf']['url']
        return FindFriendsService(service_root, self.session, self.params)

    @property
    def calendar(self):
        service_root = self.webservices['calendar']['url']
        return CalendarService(service_root, self.session, self.params)

    @property
    def contacts(self):
        service_root = self.webservices['contacts']['url']
        return ContactsService(service_root, self.session, self.params)

    def __unicode__(self):
        return 'iCloud API: %s' % self.user.get('apple_id')

    def __str__(self):
        as_unicode = self.__unicode__()
        if sys.version_info[0] >= 3:
            return as_unicode
        else:
            return as_unicode.encode('ascii', 'ignore')

    def __repr__(self):
        return '<%s>' % str(self)
