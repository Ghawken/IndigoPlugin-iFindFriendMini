"""Library base file."""
import urllib.request
import re
from typing import Any, Callable, Dict, NamedTuple, Optional, Sequence
import typing
import urllib3
from six import PY2, string_types
from uuid import uuid1
import inspect
import json
import logging
from requests import Session
import requests
from tempfile import gettempdir
from os import path, mkdir
from re import match
import http.cookiejar as cookielib
from urllib import parse
import srp
from srp import User
from typing_extensions import override

srp.rfc5054_enable()
import time
import hashlib
import base64
from datetime import datetime

#import http.cookiejar as cookielib

from pyicloud.exceptions import (
    PyiCloudFailedLoginException,
    PyiCloudAPIResponseException,
    PyiCloud2SARequiredException,
    PyiCloudServiceNotActivatedException,
)
from pyicloud.services import (
    FindMyiPhoneServiceManager,
    CalendarService,
    FindFriendsService,
    UbiquityService,
    ContactsService,
    RemindersService,
    PhotosService,
    AccountService,
    DriveService,
)
#from pyicloud.utils import get_password_from_keyring


LOGGER = logging.getLogger("Plugin.pyiCloud2fa")

HEADER_DATA = {
    "X-Apple-ID-Account-Country": "account_country",
    "X-Apple-ID-Session-Id": "session_id",
    "X-Apple-Session-Token": "session_token",
    "X-Apple-TwoSV-Trust-Token": "trust_token",
    "X-Apple-TwoSV-Trust-Eligible": "trust_eligible",
    "X-Apple-I-Rscd": "apple_rscd",
    "X-Apple-I-Ercd": "apple_ercd",
    "scnt": "scnt",
}


class PyiCloudPasswordFilter(logging.Filter):
    """Password log hider."""

    def __init__(self, password):
        super(PyiCloudPasswordFilter, self).__init__(password)

    def filter(self, record):
        message = record.getMessage()
        if self.name in message:
            record.msg = message.replace(self.name, "*" * 8)
            record.args = []

        return True


class PyiCloudSession(Session):
    """iCloud session."""

    def __init__(self, service: Any):
        self.service = service
        super().__init__()

    @override
    def request(self, method, url, **kwargs):  # pylint: disable=arguments-differ

        # Charge logging to the right service endpoint
        callee = inspect.stack()[2]
        module = inspect.getmodule(callee[0])
        request_logger = logging.getLogger("Plugin.pyiCloud_request").getChild("http")
        if self.service.password_filter not in request_logger.filters:
            request_logger.addFilter(self.service.password_filter)

        request_logger.debug("%s %s %s %s" % ( method, url, kwargs.get("data", ""), kwargs.get("json","") )  )

        has_retried = kwargs.get("retried")
        kwargs.pop("retried", None)

        response = super(PyiCloudSession, self).request(method, url, timeout=15, **kwargs )

        content_type = response.headers.get("Content-Type", "").split(";")[0]
        json_mimetypes = ["application/json", "text/json"]

        for header, value in HEADER_DATA.items():
            if response.headers.get(header):
                session_arg = value
                self.service.session_data.update(
                    {session_arg: response.headers.get(header)}
                )
       # LOGGER.debug(f"{response.headers=}\n{self.service.session_data=}")

        # Save session_data to file
        with open(self.service.session_path, "w") as outfile:
            json.dump(self.service.session_data, outfile)
            LOGGER.debug("Saved session data to file")

        # Save cookies to file
        self.cookies.save(ignore_discard=True, ignore_expires=True)
        LOGGER.debug("Cookies saved to %s" % self.service.cookiejar_path)

        if not response.ok and (content_type not in json_mimetypes
                                or response.status_code in [421, 450, 500]):
            try:
                fmip_url = self.service._get_webservice_url("findme")
                if (
                        has_retried is None
                        and response.status_code in [421, 450, 500]
                        and fmip_url is not None
                        and fmip_url in url
                ):
                    # Handle re-authentication for Find My iPhone
                    LOGGER.debug(f"\n\n\nRe-authenticating Find My iPhone service\n{fmip_url=}{url=}\n{response.ok=}\n{content_type=}\n{response.status_code=}")
                    try:
                        # If 450, authentication requires a full sign in to the account
                        service = None if response.status_code == 450 else "find"
                        self.service.authenticate(True, service)

                    except PyiCloudAPIResponseException:
                        LOGGER.debug("Re-authentication failed")
                    kwargs["retried"] = True
                    return self.request(method, url, **kwargs)
            except Exception:
                LOGGER.debug("Exception Was Passed.", exc_info=True)

            LOGGER.debug(f"Headers: {response.headers}, Reason {response.reason}, Response {response.text}")

            if has_retried is None and response.status_code in [421, 450, 500]:
                api_error = PyiCloudAPIResponseException( response.reason, response.status_code, retry=True   )
                request_logger.debug(api_error)
                kwargs["retried"] = True
                return self.request(method, url, **kwargs)

            self._raise_error(response.status_code, response.reason)

        if content_type not in json_mimetypes:
            LOGGER.debug("Response:2: status=%s ok=%s url=%s content_type=%s" % (
                response.status_code, response.ok, response.url, content_type))
            LOGGER.debug(f"Response Headers {response.headers}")
            return response

        try:
            data = response.json()
            LOGGER.debug("Data:" + str(json.dumps(data)))
          #  str(json.dumps(masterState))

        except:  # pylint: disable=bare-except
            request_logger.debug("Failed to parse response with JSON mimetype")
            return response

        #request_logger.debug(data)

        if isinstance(data, dict):
            reason = data.get("errorMessage")
            reason = reason or data.get("reason")
            reason = reason or data.get("errorReason")
            if not reason and isinstance(data.get("error"), string_types):
                reason = data.get("error")
            if not reason and data.get("error"):
                reason = "Unknown reason"

            code = data.get("errorCode")
            if not code and data.get("serverErrorCode"):
                code = data.get("serverErrorCode")

            if reason:
                self._raise_error(code, reason)

        LOGGER.debug("Response:1: status=%s ok=%s url=%s" % (
            response.status_code, response.ok, response.url))
        return response

    def _raise_error(self, code, reason):
        if (
            self.service.requires_2sa
            and reason == "Missing X-APPLE-WEBAUTH-TOKEN cookie"
        ):
            raise PyiCloud2SARequiredException(self.service.user["apple_id"])
        if code in ("ZONE_NOT_FOUND", "AUTHENTICATION_FAILED"):
            reason = (
                "Please log into https://icloud.com/ to manually "
                "finish setting up your iCloud service"
            )
            api_error = PyiCloudServiceNotActivatedException(reason, code)
            LOGGER.error(api_error)

            raise (api_error)
        if code == "ACCESS_DENIED":
            reason = (
                reason + ".  Please wait a few minutes then try again."
                "The remote servers might be trying to throttle requests."
            )
        if code in [421, 450, 500]:
            reason = "Authentication required for Account."

        if code in [503]:
            reason = "Service Temporarily Unavailable.  Please try again later."
            LOGGER.info("503 Service Temporaily Unavailable Error Received.")
        api_error = PyiCloudAPIResponseException(reason, code)
        LOGGER.debug(api_error)
        raise api_error


class PyiCloudService(object):
    """
    A base authentication class for the iCloud service. Handles the
    authentication required to access iCloud services.

    Usage:
        from pyicloud import PyiCloudService
        pyicloud = PyiCloudService('username@apple.com', 'password')
        pyicloud.iphone.location()
    """

    AUTH_ENDPOINT = "https://idmsa.apple.com/appleauth/auth"
    HOME_ENDPOINT = "https://www.icloud.com"
    SETUP_ENDPOINT = "https://setup.icloud.com/setup/ws/1"

    def __init__(
        self,
        apple_id,
        password=None,
        cookie_directory=None,
        session_directory=None,
        verify=True,
        client_id=None,
        with_family=True,
    ):
        if password is None:
            password = get_password_from_keyring(apple_id)

        self.WIDGET_KEY = "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d"
        self.user = {"accountName": apple_id, "password": password}
        self.data = {}
        # Set when signin/complete returns 409 (hsa2 challenge); read by requires_2fa
        # so callers see the correct state even though self.data has not been populated yet.
        self._2fa_required = False
        # When the 2FA challenge is delivered via SMS rather than a trusted-device
        # popup, validate_2fa_code must POST to /verify/phone/securitycode instead
        # of /verify/trusteddevice/securitycode. _2fa_sms_phone_id stores the phone
        # number id (from trustedPhoneNumbers[].id) to validate against.
        self._2fa_use_sms = False
        self._2fa_sms_phone_id = None
        self.client_id = client_id or ("auth-%s" % str(uuid1()).lower())

        self.params = {
            'clientBuildNumber': '17DHotfix5',
            'clientMasteringNumber': '17DHotfix5',
            'ckjsBuildVersion': '17DProjectDev77',
            'ckjsVersion': '2.0.5',
            'clientId': self.client_id,
        }
        self.with_family = with_family
        self.session_data = {}
        if session_directory:
            self._session_directory = session_directory
        else:
            self._session_directory = path.join(gettempdir(), "pyicloud-session")
            LOGGER.debug("Using session file %s" % self.session_path)

        try:
            with open(self.session_path) as session_f:
                self.session_data = json.load(session_f)
        except:  # pylint: disable=bare-except
            LOGGER.info("No saved Session details exists, starting afresh.")

        if not path.exists(self._session_directory):
            mkdir(self._session_directory)

        self.password_filter = PyiCloudPasswordFilter(password)
        LOGGER.addFilter(self.password_filter)

        if cookie_directory:
            self._cookie_directory = path.expanduser(path.normpath(cookie_directory))
        else:
            self._cookie_directory = path.join(gettempdir(), "pyicloud")

        if not path.exists(self._cookie_directory):
            mkdir(self._cookie_directory)

        if self.session_data.get("client_id"):
            self.client_id = self.session_data.get("client_id")
        else:
            self.session_data.update({"client_id": self.client_id})

        self.session = PyiCloudSession(self)
        self.session.verify = verify

        self.session.headers.update({
            'Origin': self.HOME_ENDPOINT,
            'Referer': '%s/' % self.HOME_ENDPOINT,
            # Use a modern, realistic User-Agent. Apple's HSA2 server silently
            # suppresses the trusted-device verification-code push when the
            # client looks suspicious (the SRP exchange still returns 409
            # hsa2, but no code is delivered). Match the User-Agent used by
            # upstream pyicloud_ipd, which is known to receive code pushes.
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/138.0.0.0 Safari/537.36'
            )
        })

        cookiejar_path = self.cookiejar_path
        self.session.cookies = cookielib.LWPCookieJar(filename=cookiejar_path)
        if path.exists(cookiejar_path):
            try:
                self.session.cookies.load(ignore_discard=True, ignore_expires=True)
                LOGGER.debug("Read cookies from %s" % cookiejar_path)
            except:  # pylint: disable=bare-except
                # Most likely a pickled cookiejar from earlier versions.
                # The cookiejar will get replaced with a valid one after
                # successful authentication.
                LOGGER.warning("Failed to read cookiejar %s" % cookiejar_path)

        LOGGER.debug("************ Headers for PyiCloud Service ***************")
        LOGGER.debug(str(self.session.headers))
        self.authenticate()

        self._drive = None
        self._files = None
        self._photos = None


    def compute_hashcash(self, challenge, bits):
        counter = 0
        date_str = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        bits = int(bits)

        while True:
            # Hashcash string format: ver:bits:date:resource:rand1:counter
            hashcash_str = f"1:{bits}:{date_str}:{challenge}:{counter}"
            sha1_hash = hashlib.sha1(hashcash_str.encode('utf-8')).hexdigest()

            # Convert hash to binary and check if it has the required number of leading zeros
            hash_binary = bin(int(sha1_hash, 16))[2:].zfill(160)
            if hash_binary.startswith('0' * bits):
                return hashcash_str
            counter += 1

    def make_hashcash(bits, challenge):
        """
        Generates a hashcash string compatible with Apple's specifications.

        Parameters:
            bits (str): The number of leading zero bits required in the hash.
            challenge (str): The challenge string provided by Apple.

        Returns:
            str: The generated hashcash string.
        """
        version = 1
        date = datetime.now().strftime("%Y%m%d%H%M%S")
        counter = 0

        while True:
            # Construct the hashcash string
            # Note: There's an empty field between challenge and counter, represented by "::"
            hc = f"{version}:{bits}:{date}:{challenge}::{counter}"

            # Compute SHA1 digest
            sha1_digest = hashlib.sha1(hc.encode('utf-8')).digest()

            # Convert digest to binary string
            digest_bits = ''.join(f"{byte:08b}" for byte in sha1_digest)

            # Check if the first 'bits' bits are all zero
            if int(digest_bits[:int(bits)], 2) == 0:
                return hc

            counter += 1
    def fetch_hashcash(self):
        """
        Fetches hashcash by making a GET request to Apple's authentication endpoint.

        Returns:
            str or None: The generated hashcash string if successful, else None.
        """
        init_url = f"https://idmsa.apple.com/appleauth/auth/signin?widgetKey={self.WIDGET_KEY}"
        headers = {
            'Accept': 'application/json, text/javascript',
            'X-Requested-With': 'XMLHttpRequest'
        }
        try:
            response = requests.get(init_url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch hashcash: {e}")
            return None

        # Extract headers
        bits = response.headers.get("X-Apple-HC-Bits")
        challenge = response.headers.get("X-Apple-HC-Challenge")

        if bits is None or challenge is None:
            LOGGER.debug("Unable to find 'X-Apple-HC-Bits' and 'X-Apple-HC-Challenge' to make hashcash")
            return None

        # Generate hashcash
        hashcash = self.make_hashcash(bits, challenge)
        LOGGER.debug(f"{hashcash=}")
        return hashcash
    def authenticate(self, force_refresh:bool=False, service:Optional[Any]=None) -> None:
        """
        Handles authentication using SRP protocol and manages session tokens.
        """
        login_successful = False
        username = self.user['accountName']
        password = self.user["password"]

        if self.session_data.get("session_token") and not force_refresh:
            # Check if session token is still valid
            LOGGER.debug(f"Checking Session Token Validity...")
            try:
                req = self.session.post(
                    f"{self.SETUP_ENDPOINT}/validate",
                    params=self.params,
                    data="null"
                )
                self.data = req.json()
                if 'dsInfo' in self.data:
                    if 'dsid' in self.data['dsInfo']:
                        if 'dsid' in self.params:  # already checked above, but recheck
                            self.params.update({"dsid": self.data["dsInfo"]["dsid"]})
                login_successful = True
                LOGGER.debug("Session token validation succeeded.")
                # If Apple's validate response confirms the browser/session is
                # trusted and no challenge is required, ensure the sticky
                # _2fa_required flag (set on a previous 409 hsa2) is cleared
                # so requires_2fa stops claiming 2FA is still needed.
                try:
                    if (
                        self.data.get("dsInfo", {}).get("hsaVersion", 0) == 2
                        and not self.data.get("hsaChallengeRequired", False)
                        and self.data.get("hsaTrustedBrowser", False)
                    ):
                        self._2fa_required = False
                except Exception:
                    pass
            except PyiCloudAPIResponseException:
                LOGGER.debug("Invalid authentication token, will log in from scratch.")

        if not login_successful and service is not None:
            app = self.data["apps"][service]
            if "canLaunchWithOneFactor" in app and app["canLaunchWithOneFactor"]:
                LOGGER.debug(
                    "Authenticating as %s for %s", self.user["accountName"], service
                )
                try:
                    self._authenticate_with_credentials_service(service)
                    login_successful = True
                except Exception:
                    LOGGER.debug(
                        "Could not log into service. Attempting brand new login."
                    )

        if not login_successful:
            headers = self._get_auth_headers()
            # Apple's auth endpoint expects Origin/Referer pointing at
            # idmsa.apple.com (not www.icloud.com which is the session
            # default). Mismatched origins on /signin/init and
            # /signin/complete cause Apple's HSA2 system to suppress the
            # verification-code push to trusted devices. Match upstream
            # pyicloud_ipd here.
            headers["Origin"] = "https://idmsa.apple.com"
            headers["Referer"] = "https://idmsa.apple.com/"
            if self.session_data.get("scnt"):
                headers["scnt"] = self.session_data.get("scnt")
            if self.session_data.get("session_id"):
                headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")

            LOGGER.debug("************ Headers for Token Session ***************")
            LOGGER.debug(str(headers))
            class SrpPassword():
                def __init__(self, password: str):
                    self.password = password

                def set_encrypt_info(self, protocol: str, salt: bytes, iterations: int, key_length: int):
                    self.protocol = protocol
                    self.salt = salt
                    self.iterations = iterations
                    self.key_length = 32 # key_length

                def encode(self):
                    key_length = 32
                    if (self.protocol == 's2k_fo'):
                        password_hash = hashlib.sha256(self.password.encode('utf-8')).hexdigest()[:-1]
                    else:
                        password_hash = hashlib.sha256(self.password.encode('utf-8')).digest()

                    return hashlib.pbkdf2_hmac('sha256', password_hash, salt, iterations, key_length)


            LOGGER.debug("Authenticating as %s using SRP" % self.user["accountName"])

            srp_password = SrpPassword(self.user["password"])
            srp.rfc5054_enable()
            srp.no_username_in_x()
            usr = srp.User(self.user["accountName"], srp_password, hash_alg=srp.SHA256, ng_type=srp.NG_2048)

            uname, A = usr.start_authentication()

            # Step 3: Send 'A' to Apple and receive 'B' and 'salt'
            init_url = '%s/signin/init' % self.AUTH_ENDPOINT

            init_data = {
                'a': base64.b64encode(A).decode(),
                'accountName': uname,
                'protocols': ['s2k', 's2k_fo']
            }

            LOGGER.debug(f"SRP init URL: {init_url}")
            LOGGER.debug(f"SRP init headers: {headers}")
            LOGGER.debug(f"SRP init data: {init_data}")

            try:
                init_resp = self.session.post(init_url, data=json.dumps(init_data), headers=headers)
                #init_resp.raise_for_status()
                LOGGER.debug("SRP init request returned (status=%s)" % init_resp.status_code)

            except PyiCloudAPIResponseException as e:
                msg = f"SRP init failed: {e}"
                LOGGER.debug(msg)
                raise PyiCloudFailedLoginException(msg, e) from e

            init_resp_data = init_resp.json()
            LOGGER.debug(f"SRP init response status: {init_resp.status_code}")
            LOGGER.debug(f"SRP init response content: {init_resp.text}")
            LOGGER.debug(f"SRP init response Headers: {init_resp.headers}")
            LOGGER.debug(f"{init_resp_data=}")

            scnt = self.session_data.get("scnt")
            if scnt:
                headers["scnt"] = scnt
            session_id = self.session_data.get("session_id")
            if session_id:
                headers["X-Apple-ID-Session-Id"] = session_id

            salt = base64.b64decode(init_resp_data['salt'])
            b = base64.b64decode(init_resp_data['b'])
            protocol = init_resp_data['protocol']
            c = init_resp_data['c']
            iterations = init_resp_data['iteration']
            key_length = 32

            srp_password.set_encrypt_info(protocol, salt, iterations, key_length)

            m1 = usr.process_challenge(salt, b)
            m2 = usr.H_AMK

            if not m1:
                raise Exception("Failed to process challenge: m1 is None")
            LOGGER.debug(f" m1 (Python): {m1}  m2 (Python): {m2}")

            complete_url = '%s/signin/complete?isRememberMeEnabled=false' % self.AUTH_ENDPOINT
           # headers.update( {
          #      "X-Apple-HC": hashcash_token    }
          #  )

            complete_data = {
                "accountName": uname,
                "c": c,
                "m1": base64.b64encode(m1).decode(),
                "m2": base64.b64encode(m2).decode(),
                "rememberMe": True,
                "trustTokens": [],
            }
            if self.session_data.get("trust_token"):
                complete_data["trustTokens"] = [self.session_data.get("trust_token")]

            LOGGER.debug(f"Sending: Complete_data\n {json.dumps(complete_data)}\n")
            LOGGER.debug(f"With Complete Headers:\n\n{headers}")
            # Send 'm1' to the server

            try:
                LOGGER.debug("Posting SRP signin/complete...")
                complete_resp = self.session.post(
                    "%s/signin/complete" % self.AUTH_ENDPOINT,
                    params={"isRememberMeEnabled": "true"},
                    data=json.dumps(complete_data),
                    headers=headers,
                )
            except PyiCloudAPIResponseException as error:
                LOGGER.debug("SRP signin/complete failed: %s" % error)
                msg = "Invalid username/password combination."
                raise PyiCloudFailedLoginException(msg, error) from error

            LOGGER.debug("SRP signin/complete returned (status=%s)" % complete_resp.status_code)
            complete_resp_data = complete_resp.json()

            LOGGER.debug(f"{complete_resp_data}")
            LOGGER.debug(f"Complete Headers: \n\n{complete_resp.headers}\n\n")
            if complete_resp.status_code == 409:
                LOGGER.info("Two Factor Authentication enabled for this Account.  Please enter Code and Press Button")
                self._2fa_required = True

                # Trigger Apple to push the 6-digit verification code popup
                # to all trusted devices. Apple does NOT push the code
                # automatically after signin/complete returns 409 hsa2 — the
                # client must follow up with a GET to /appleauth/auth
                # (carrying the same scnt + X-Apple-ID-Session-Id headers).
                # That GET is what Apple interprets as "client is waiting for
                # 2FA" and dispatches the push fan-out. Reference:
                # gcobb321/icloud3_v3 apple_acct.py (is_session_trusted_auth_check).
                try:
                    auth_url = "%s/auth" % self.AUTH_ENDPOINT
                    auth_headers = self._get_auth_headers({"Accept": "application/json"})
                    auth_headers["Origin"] = "https://idmsa.apple.com"
                    auth_headers["Referer"] = "https://idmsa.apple.com/"
                    if self.session_data.get("scnt"):
                        auth_headers["scnt"] = self.session_data.get("scnt")
                    if self.session_data.get("session_id"):
                        auth_headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")
                    LOGGER.debug("Triggering 2FA device push: GET %s" % auth_url)
                    push_resp = self.session.get(auth_url, headers=auth_headers)
                    LOGGER.debug("2FA device push trigger returned (status=%s)" % push_resp.status_code)
                    if push_resp.status_code in (200, 409):
                        # Parse the response to see what verification channels are
                        # actually available. Modern Apple ID accounts often only
                        # expose trustedPhoneNumbers (SMS) here — no trustedDevices
                        # popup will appear in that case, so we must explicitly
                        # request the SMS code be sent to the trusted phone.
                        try:
                            auth_data = push_resp.json()
                        except Exception:
                            auth_data = {}

                        trusted_devices = auth_data.get("trustedDevices") or []
                        phone_block = auth_data.get("phoneNumberVerification") or auth_data
                        trusted_phones = phone_block.get("trustedPhoneNumbers") or []

                        if trusted_devices:
                            # Apple should be pushing the popup to trusted devices
                            # via APNS — nothing else to do here.
                            LOGGER.info("Verification code pushed to trusted devices.")
                        elif trusted_phones:
                            # No trusted device popup channel — this account is in
                            # SMS-only 2FA state for this flow. Request the SMS by
                            # calling PUT /appleauth/auth/verify/phone, mirroring
                            # gcobb321/icloud3_v3 (request_auth_code_via_text_msg).
                            phone_id = trusted_phones[0].get("id", 1)
                            obfuscated = trusted_phones[0].get(
                                "numberWithDialCode",
                                trusted_phones[0].get("obfuscatedNumber", "trusted phone"),
                            )
                            sms_headers = self._get_auth_headers({"Accept": "application/json"})
                            sms_headers["Origin"] = "https://idmsa.apple.com"
                            sms_headers["Referer"] = "https://idmsa.apple.com/"
                            if self.session_data.get("scnt"):
                                sms_headers["scnt"] = self.session_data.get("scnt")
                            if self.session_data.get("session_id"):
                                sms_headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")
                            sms_url = "%s/verify/phone" % self.AUTH_ENDPOINT
                            sms_body = {"phoneNumber": {"id": phone_id}, "mode": "sms"}
                            try:
                                sms_resp = self.session.put(
                                    sms_url, data=json.dumps(sms_body), headers=sms_headers
                                )
                                LOGGER.debug(
                                    "SMS request PUT %s returned status=%s"
                                    % (sms_url, sms_resp.status_code)
                                )
                                if sms_resp.status_code in (200, 204):
                                    self._2fa_use_sms = True
                                    self._2fa_sms_phone_id = phone_id
                                    LOGGER.info(
                                        "Verification code sent via SMS to %s. "
                                        "Enter the code in the Plugin Config."
                                        % obfuscated
                                    )
                                else:
                                    LOGGER.info(
                                        "SMS verification request returned %s; "
                                        "the code may not arrive." % sms_resp.status_code
                                    )
                            except Exception as sms_err:
                                LOGGER.debug("Exception requesting SMS code: %s" % sms_err)
                        else:
                            LOGGER.info(
                                "No trusted devices or phone numbers reported by Apple; "
                                "the verification code may not appear automatically."
                            )
                    else:
                        LOGGER.info("Trusted Device push request returned %s; the code may not appear on devices." % push_resp.status_code)
                except Exception as push_err:
                    LOGGER.debug("Exception triggering 2FA device push: %s" % push_err)

                return
                #Dont validate token and dont try to assign webservices which can be none
            elif complete_resp.status_code == 200:
                LOGGER.info("Account Successfully logged in.")
                login_successful = True
                self._2fa_required = False
                if 'dsInfo' in self.data and 'dsid' in self.data['dsInfo']:
                    self.params.update({"dsid": self.data["dsInfo"]["dsid"]})
                self._authenticate_with_token()
            else:
                LOGGER.debug(f"{complete_resp.status_code}  Returned from Authenticate Complete Call")

        if login_successful:
            self._webservices = self.data["webservices"]
            LOGGER.debug("Authentication completed successfully")
        else:
            LOGGER.info("Login was not successful.  Please check username and password combination.")
            LOGGER.info("If recent changes, consider deleting plugin acccount via delete button at bottom of plugin Config Page and trying again")
            raise PyiCloudFailedLoginException("Login was not successful.", "Error.")

        ##
    def _authenticate_with_credentials_service(self, service: str) -> None:
        """Authenticate to a specific service using credentials."""
        data = {
            "appName": service,
            "apple_id": self.user["accountName"],
            "password": self.user["password"],
        }

        try:
            self.session.post(
                "%s/accountLogin" % self.SETUP_ENDPOINT, data=json.dumps(data)
            )

            self.data = self._validate_token()
        except PyiCloudAPIResponseException as error:
            msg = "Invalid email/password combination."
            raise PyiCloudFailedLoginException(msg, error) from error
    def authenticate_old(self, force_refresh=False):
        """
        Handles authentication, and persists cookies so that
        subsequent logins will not cause additional e-mails from Apple.
        """
        LOGGER.debug(u"{0:=^130}".format(""))
        LOGGER.debug("Self.Params:="+str(self.params))
        LOGGER.debug(u"{0:=^130}".format(""))
        login_successful = False
        if self.session_data.get("session_token") and not force_refresh and 'dsid' in self.params:
            LOGGER.debug("Checking session token validity")
            try:
                req = self.session.post("%s/validate" % self.SETUP_ENDPOINT, params=self.params, data="null")
                LOGGER.debug("Session token is still valid")
                self.data = req.json()
                LOGGER.debug("Session Data Returned:" + str(self.data))
                login_successful = True
                ## check for correct valid using dsid
                if 'dsInfo' in self.data:
                    if 'dsid' in self.data['dsInfo']:
                        if 'dsid' in self.params:  # already checked above, but recheck
                            self.params.update({"dsid": self.data["dsInfo"]["dsid"]}) ## should already be set, but no harm...
                    else:
                        login_successful = False
                        self.logger.debug(u"No DSID in return data:"+str(self.data))
                else:
                    login_successful = False
                    self.logger.debug(u"No DSID in return data:" + str(self.data))


            except PyiCloudAPIResponseException:
                LOGGER.debug("Invalid authentication token, will log in from scratch.")

        if not login_successful:
            LOGGER.debug("Authenticating as %s" % self.user["accountName"])

            data = dict(self.user)
            data["rememberMe"] = True
            data["trustTokens"] = []
            if self.session_data.get("trust_token"):
                data["trustTokens"] = [self.session_data.get("trust_token")]

            headers = self._get_auth_headers()
            if self.session_data.get("scnt"):
                headers["scnt"] = self.session_data.get("scnt")
            if self.session_data.get("session_id"):
                headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")
            LOGGER.debug("************ Headers for Token Session ***************")
            LOGGER.debug(str(headers))

            try:
                LOGGER.debug(f"/signin \n\nJson Data: {json.dumps(data)} and {headers=}")
                req = self.session.post(
                    "%s/federate" % self.AUTH_ENDPOINT,
                    params={"isRememberMeEnabled": "true" },
                    data=json.dumps(data),
                    headers=headers,
                )
            except PyiCloudAPIResponseException as error:
                msg = "Invalid email/password combination."
                raise PyiCloudFailedLoginException(msg, error)

            LOGGER.debug(f"**** Success.  Headers:{req.headers}  {req}")

            if "X-Apple-Repair-Session-Token" in req.headers:
                LOGGER.debug(f"*************** Repair Token Found: NON 2fa being stuffed.")
                self._bypass_Repair2FA(req)


            self.params.update({
                "dsid": self.data.get("dsInfo").get("dsid")
            })
            #self.trust_session()  ## delete me afte rlogging

        self._webservices = self.data["webservices"]
        self._authenticate_with_token()
        LOGGER.debug("Authentication completed successfully")

## Move to SRP



    def _get_auth_non2FA_headers(self, overrides=None):
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "X-Apple-OAuth-Client-Id": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
            "X-Apple-OAuth-Client-Type": "firstPartyAuth",
            "X-Apple-OAuth-Redirect-URI": "https://www.icloud.com",
            "X-Apple-OAuth-Require-Grant-Code": "true",
            "X-Apple-OAuth-Response-Mode": "web_message",
            "X-Apple-OAuth-Response-Type": "code",
            "X-Apple-Frame-Id": self.client_id,
            "X-Apple-Domain-Id": 3,
            "X-Apple-OAuth-State": self.client_id,
            "X-Apple-Widget-Key": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
        }
        if overrides:
            headers.update(overrides)
        return headers

    def _bypass_Repair2FA(self, response):
        LOGGER.info("Non 2FA being used, Apple wants to repair this/upgrade this, attempting to bypass and resume usual login")

        http = urllib3.PoolManager()

        old_location = f"{response.headers['location']}"
        widgetKey = parse.parse_qs(parse.urlparse(old_location).query)['widgetKey'][0]
        ##  if &rv=1 fails (!) That was 2 hours I won't get back
        location = old_location.replace("&rv=1","&rv=3")
        LOGGER.debug(f"Location:{location}")
        needuseragent = {}
        needuseragent['Content-Type'] = 'application/json'
        needuseragent['Accept'] ='text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        needuseragent["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

        LOGGER.debug(f"Using URL: {location}\n Headers:\n {needuseragent}")
        missed_req = http.request("GET", url=location, headers=needuseragent)

        LOGGER.debug(f"Missed_Req:url {location}\n{missed_req}, \n widgetKey {widgetKey}, \n missed_req headers {missed_req.headers}")
        LOGGER.debug(f"Status of Missed one: {missed_req.status}")
        #LOGGER.error(f"Data returned:{missed_req.content}")

        LOGGER.debug("Need to get SAet-Cookie aidsp")
        LOGGER.debug(f'{missed_req.headers["Set-Cookie"]}')
        cookies =f'{missed_req.headers["Set-Cookie"]}'
        result = re.search('aidsp=(.*); Domain=', cookies)  ## Split off aidsp from the cookie string.
        LOGGER.debug(f"Result cookies = {result.group(1)}")
        SessionID = result.group(1)

        url = "https://appleid.apple.com/account/manage/repair/options"
        new_headers =  {} #response.headers
        new_headers['scnt'] = missed_req.headers['scnt']
        new_headers['X-Apple-ID-Session-Id'] = SessionID
        ## Session ID comes from set-Cookie aidsp, from the repair Widget request
        new_headers['X-Apple-Session-Token'] = response.headers['X-Apple-Repair-Session-Token']
        new_headers['X-Apple-Skip-Repair-Attributes'] = '[]'
        new_headers['X-Apple-Widget-Key'] = widgetKey
        new_headers['Content-Type'] = 'application/json'
        new_headers['X-Requested-With'] = 'XMLHttpRequest'
        new_headers['Accept'] = 'application/json, text/javascript'
        #new_headers['X-Apple-OAuth-Context']= missed_req.headers['X-Apple-OAuth-Context']
     #   new_headers['Referer'] = "https://appleid.apple.com/"
    #    new_headers['Host'] = "appleid.apple.com"
        new_headers['User-Agent']= "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

        #    req = self.session.post("%s/validate" % self.SETUP_ENDPOINT, params=self.params, data="null")
        LOGGER.debug(f"myattempt: url: {url} \n new_headers {new_headers}")
        myattempt = http.request("GET", url=url, headers=new_headers)
        LOGGER.debug(f"Try myattempt: {myattempt}, {myattempt.headers} ")

        LOGGER.debug(f"Status of MyAttempt: {myattempt.status}")

        next_headers = {}
        url = "https://appleid.apple.com/account/security/upgrade/setuplater"
        next_headers['scnt'] = missed_req.headers['scnt']
        next_headers['X-Apple-ID-Session-Id'] = SessionID
        next_headers['X-Apple-Session-Token'] = myattempt.headers['X-Apple-Session-Token']
        next_headers['X-Apple-Skip-Repair-Attributes'] = '["hsa2_enrollment"]'
        next_headers['X-Apple-Widget-Key'] = widgetKey
        next_headers['Content-Type'] = 'application/json'
        next_headers['X-Requested-With'] = 'XMLHttpRequest'
        next_headers['Accept'] = 'application/json, text/javascript'
        next_headers['User-Agent']= "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

        LOGGER.debug(f"NextAttempt: url: {url} \n new_headers {next_headers}")
        nextattempt = http.request("GET", url=url, headers=next_headers)
        LOGGER.debug(f"Try nextattempt: {nextattempt}, {nextattempt.headers}")
        LOGGER.debug(f"Status of NextAttempt: {nextattempt.status}")

        last_headers =self._get_auth_non2FA_headers()

        url = "https://idmsa.apple.com/appleauth/auth/repair/complete"
        last_headers['scnt'] = missed_req.headers['scnt']

        last_headers['X-Apple-ID-Session-Id'] = SessionID
        #next_headers['X-Apple-Session-Token'] = myattempt.headers['X-Apple-Session-Token']
        last_headers['X-Apple-Repair-Session-Token'] = myattempt.headers['X-Apple-Session-Token']
        last_headers['X-Apple-Widget-Key'] = widgetKey

        last_headers['Content-Type'] = 'application/json'
        last_headers['X-Requested-With'] = 'XMLHttpRequest'
        last_headers['Accept'] = 'application/json;charset=utf-8'

        #last_headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
       # LOGGER.debug(f'X-Auth: {response.headers["X-Apple-Auth-Attributes"]}')
       # last_headers["X-Apple-Auth-Attributes"]= response.headers["X-Apple-Auth-Attributes"]
       # last_headers["Content-Length"]=0
       # last_headers["Origin"]= "https://idmsa.apple.com"
       # last_headers["Referer"]= "https://idmsa.apple.com/"
       # last_headers["Host"] = "idmsa.apple.com"
       # last_headers["X-Apple-Locale"] = "en_GB"
       # LOGGER.error(f'Response Set-Cookie: {response.headers["Set-Cookie"]}')
       # last_headers["Set-Cookie"]= response.headers["Set-Cookie"]
        #data = json.dumps({})
       # last_headers["X-Apple-I-FD-Client-Info"]= '{"U":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36","L":"en-GB","Z":"GMT+11:00","V":"1.1","F":"Fta44j1e3NlY5BNlY5BSs5uQ32SCVc8NTjN37FSHmr9k.uJtHoqvynx9MsFyxY25CKw..BN.Fg4JRK8mcK9rTKIwBfxFETlWY5BNlYJNNlY5QB4bVNjMk.3v5"}'
        data = {}
        data["trustTokens"] = []
        if self.session_data.get("trust_token"):
            data["trustTokens"] = [self.session_data.get("trust_token")]


        #if self.session_data.get("trust_token"):
        #    data["trustTokens"] = [self.session_data.get("trust_token")]


        last_attempt = http.request("POST", url=url, body=json.dumps(data), headers=last_headers)
        LOGGER.debug(f"Try last: Status:{last_attempt.status} ")
        LOGGER.debug(f" Total: {last_attempt},\nHeaders: {last_attempt.headers} ")
        LOGGER.debug(f"lastOne: url:\n{url}\n last_headers:\n{last_headers}")
        LOGGER.debug(f" Last_Attempt: {last_attempt.data} ")

        if last_attempt.status == 204:
            LOGGER.info("Repair of non 2FA skipped, successfully it would seem. Hopefully logins normally now")
        return

    def _authenticate_with_token(self):
        """Authenticate using session token."""
        #LOGGER.debug(f"{self.session_data}")
        data = {
            "accountCountryCode": self.session_data.get("account_country"),
            "dsWebAuthToken": self.session_data.get("session_token"),
            "extended_login": True,
            "trustToken": self.session_data.get("trust_token", ""),
        }

        LOGGER.debug("************ Headers for _authenicate with Token /accountLogin Session ***************")
        LOGGER.debug(str(self.session.headers))
        try:
            req = self.session.post(
                "%s/accountLogin?clientBuildNumber=2426&Hotfix45Project52&clientMasteringNumber=2021B29&clientId=%s" % (self.SETUP_ENDPOINT, self.client_id[5:]), data=json.dumps(data)
            )
        except PyiCloudAPIResponseException as error:
            LOGGER.debug("/accountLogin failed during token authentication: %s" % error)
            msg = "Invalid authentication token."
            raise PyiCloudFailedLoginException(msg, error)

        LOGGER.debug("/accountLogin returned (status=%s) during token authentication." % req.status_code)
        self.data = req.json()
        self._update_dsid(self.data)

    def _update_dsid(self,data):
        try:
            LOGGER.debug((f"updating dsid {data}"))
            if 'dsInfo' in data:  ## check self.data returned and contains dsid
                if 'dsid' in data['dsInfo']:        # as above
                    self.params["dsid"]= str(data["dsInfo"]["dsid"])
            else:
                if 'dsid' in self.params:
                    self.params.pop("dsid")  ## if no dsid given delete it from self.params - until returned.  Otherwise is passing default incorrect dsid
        except:
            LOGGER.debug(u"Error setting dsid field.")
            if 'dsid' in self.params:
                self.params.pop("dsid")  ## if error, self.data None/empty delete
        return

    def _get_auth_headers(self, overrides=None):
        headers = {
            "Accept": "application/json, text/javascript",
            "Content-Type": "application/json",
            "X-Apple-OAuth-Client-Id": self.WIDGET_KEY,
            "X-Apple-OAuth-Client-Type": "firstPartyAuth",
            "X-Apple-OAuth-Redirect-URI": "https://www.icloud.com",
            "X-Apple-OAuth-Require-Grant-Code": "true",
            "X-Apple-OAuth-Response-Mode": "web_message",
            "X-Apple-OAuth-Response-Type": "code",
            "X-Apple-OAuth-State": self.client_id,
            "X-Apple-Widget-Key": self.WIDGET_KEY,
        }
        if overrides:
            headers.update(overrides)
        return headers

    @property
    def cookiejar_path(self):
        """Get path for cookiejar file."""
        return path.join(
            self._cookie_directory,
            "".join([c for c in self.user.get("accountName") if match(r"\w", c)]),
        )

    @property
    def session_path(self):
        """Get path for session data file."""
        return path.join(
            self._session_directory,
            "".join([c for c in self.user.get("accountName") if match(r"\w", c)]),
        )

    @property
    def requires_2sa(self):
        """Returns True if two-step authentication is required."""
        return self.data.get("dsInfo", {}).get("hsaVersion", 0) >= 1 and (
            self.data.get("hsaChallengeRequired", False) or not self.is_trusted_session
        )

    @property
    def requires_2fa(self):
        """Returns True if two-factor authentication is required."""

        # If signin/complete returned 409 (hsa2 challenge), self.data is empty
        # at this point but 2FA is definitely required.
        if getattr(self, "_2fa_required", False):
            return True

        return self.data.get("dsInfo",{}).get("hsaVersion", 0) == 2 and (
            self.data.get("hsaChallengeRequired", False) or not self.is_trusted_session
        )
        return None

    @property
    def is_trusted_session(self):
        """Returns True if the session is trusted."""
        return self.data.get("hsaTrustedBrowser", False)

    @property
    def trusted_devices(self):
        """Returns devices trusted for two-step authentication."""
        request = self.session.get(
            "%s/listDevices" % self.SETUP_ENDPOINT, params=self.params
        )
        return request.json().get("devices")

    def send_verification_code(self, device):
        """Requests that a verification code is sent to the given device."""
        data = json.dumps(device)
        request = self.session.post(
            "%s/sendVerificationCode" % self.SETUP_ENDPOINT,
            params=self.params,
            data=data,
        )
        return request.json().get("success", False)

    def validate_verification_code(self, device, code):
        """Verifies a verification code received on a trusted device."""
        device.update({"verificationCode": code, "trustBrowser": True})
        data = json.dumps(device)

        try:
            self.session.post(
                "%s/validateVerificationCode" % self.SETUP_ENDPOINT,
                params=self.params,
                data=data,
            )
        except PyiCloudAPIResponseException as error:
            if error.code == -21669:
                # Wrong verification code
                return False
            raise

        self.trust_session()
        self._2fa_required = False

        return not self.requires_2sa

    def validate_2fa_code(self, code):
        """Verifies a verification code received via Apple's 2FA system (HSA2)."""
        # When the code was delivered via SMS (no trusted device popup was
        # available), the validation endpoint and payload differ.
        if getattr(self, "_2fa_use_sms", False):
            phone_id = self._2fa_sms_phone_id or 1
            data = {
                "phoneNumber": {"id": phone_id},
                "securityCode": {"code": code},
                "mode": "sms",
            }
            verify_url = "%s/verify/phone/securitycode" % self.AUTH_ENDPOINT
        else:
            data = {"securityCode": {"code": code}}
            verify_url = "%s/verify/trusteddevice/securitycode" % self.AUTH_ENDPOINT

        headers = self._get_auth_headers({"Accept": "application/json"})
        # Match the Origin/Referer used during the SRP signin flow so Apple
        # treats this as the same client that requested the code.
        headers["Origin"] = "https://idmsa.apple.com"
        headers["Referer"] = "https://idmsa.apple.com/"

        if self.session_data.get("scnt"):
            headers["scnt"] = self.session_data.get("scnt")

        if self.session_data.get("session_id"):
            headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")

        LOGGER.debug(f"Headers for 2FA Code\n\n\n{headers}")

        try:
            self.session.post(
                verify_url,
                data=json.dumps(data),
                headers=headers,
            )
        except PyiCloudAPIResponseException as error:
            if error.code == -21669:
                # Wrong verification code
                LOGGER.info("*** Code verification failed. ***")
                return False
            raise

        LOGGER.info("Code verification successful.")

        self.trust_session()
        # Clear the sticky 2FA-required flag set on the 409 hsa2 branch so
        # requires_2fa stops returning True now that the code has been
        # accepted and trust_session has refreshed self.data.
        self._2fa_required = False
        self._2fa_use_sms = False
        self._2fa_sms_phone_id = None
        return not self.requires_2sa

    def trust_session(self):
        """Request session trust to avoid user log in going forward."""
        headers = self._get_auth_headers()

        if self.session_data.get("scnt"):
            headers["scnt"] = self.session_data.get("scnt")

        if self.session_data.get("session_id"):
            headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")

        #LOGGER.info("************ Headers for Trust Session ***************")
       # LOGGER.info(str(headers))


        try:
            self.session.get(
                "%s/2sv/trust" % self.AUTH_ENDPOINT,
                headers=headers,
            )
            self._authenticate_with_token()
            return True
        except PyiCloudAPIResponseException:
            LOGGER.info("Session trust failed.  Appears to be incorrect Code.")
            return False

    def _get_webservice_url(self, ws_key):
        """Get webservice URL, raise an exception if not exists."""
        try:
            if self._webservices.get(ws_key) is None:
               return None
            return self._webservices[ws_key]["url"]
        except:
            LOGGER.debug("Exception Ignored getting webservice url")
            return None

    @property
    def devices(self):
        """Returns all devices."""
        service_root = self._get_webservice_url("findme")
        return FindMyiPhoneServiceManager(
            service_root, self.session, self.params, self.with_family
        )
        #return FindFriendsService(service_root, self.session, self.params)
      #  return FindMyiPhoneServiceManager(
     ##    )

    @property
    def iphone(self):
        """Returns the iPhone."""
        return self.devices[0]

    @property
    def account(self):
        """Gets the 'Account' service."""
        service_root = self._get_webservice_url("account")
        return AccountService(service_root, self.session, self.params)

    @property
    def files(self):
        """Gets the 'File' service."""
        if not self._files:
            service_root = self._get_webservice_url("ubiquity")
            self._files = UbiquityService(service_root, self.session, self.params)
        return self._files

    @property
    def friends(self):
        service_root = self._get_webservice_url("findme")
        return FindMyiPhoneServiceManager(service_root, self.session, self.params)
        #return FindFriendsService(service_root, self.session, self.params)

    @property
    def photos(self):
        """Gets the 'Photo' service."""
        if not self._photos:
            service_root = self._get_webservice_url("ckdatabasews")
            self._photos = PhotosService(service_root, self.session, self.params)
        return self._photos

    @property
    def calendar(self):
        """Gets the 'Calendar' service."""
        service_root = self._get_webservice_url("calendar")
        return CalendarService(service_root, self.session, self.params)

    @property
    def contacts(self):
        """Gets the 'Contacts' service."""
        service_root = self._get_webservice_url("contacts")
        return ContactsService(service_root, self.session, self.params)

    @property
    def reminders(self):
        """Gets the 'Reminders' service."""
        service_root = self._get_webservice_url("reminders")
        return RemindersService(service_root, self.session, self.params)

    @property
    def drive(self):
        """Gets the 'Drive' service."""
        if not self._drive:
            self._drive = DriveService(
                service_root=self._get_webservice_url("drivews"),
                document_root=self._get_webservice_url("docws"),
                session=self.session,
                params=self.params,
            )
        return self._drive

    def __str__(self):
        return "iCloud API: %s" % self.user.get("accountName")

    def __str__(self):
        as_str = self.__str__()
        if PY2:
            return as_str.encode("utf-8", "ignore")
        return as_str

    def __repr__(self):
        return "<%s>" % str(self)