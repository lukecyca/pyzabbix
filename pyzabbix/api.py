# pylint: disable=wrong-import-order

import logging
from typing import Mapping, Optional, Sequence, Tuple, Union
from warnings import warn

from packaging.version import Version
from requests import Session

__all__ = [
    "ZabbixAPI",
    "ZabbixAPIException",
    "ZabbixAPIMethod",
    "ZabbixAPIObject",
    "ZabbixAPIObjectClass",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

ZABBIX_5_4_0 = Version("5.4.0")
ZABBIX_6_4_0 = Version("6.4.0")


class ZabbixAPIException(Exception):
    """Generic Zabbix API exception

    Codes:
      -32700: invalid JSON. An error occurred on the server while
              parsing the JSON text (typo, wrong quotes, etc.)
      -32600: received JSON is not a valid JSON-RPC Request
      -32601: requested remote-procedure does not exist
      -32602: invalid method parameters
      -32603: Internal JSON-RPC error
      -32400: System error
      -32300: Transport error
      -32500: Application error
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.error = kwargs.get("error", None)


# pylint: disable=too-many-instance-attributes
class ZabbixAPI:
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        server: str = "http://localhost/zabbix",
        session: Optional[Session] = None,
        use_authenticate: bool = False,
        timeout: Optional[Union[float, int, Tuple[int, int]]] = None,
        detect_version: bool = True,
    ):
        """
        :param server: Base URI for zabbix web interface (omitting /api_jsonrpc.php)
        :param session: optional pre-configured requests.Session instance
        :param use_authenticate: Use old (Zabbix 1.8) style authentication
        :param timeout: optional connect and read timeout in seconds, default: None
                        If you're using Requests >= 2.4 you can set it as
                        tuple: "(connect, read)" which is used to set individual
                        connect and read timeouts.
        :param detect_version: autodetect Zabbix API version
        """
        self.session = session or Session()

        # Default headers for all requests
        self.session.headers.update(
            {
                "Content-Type": "application/json-rpc",
                "User-Agent": "python/pyzabbix",
                "Cache-Control": "no-cache",
            }
        )

        self.use_authenticate = use_authenticate
        self.use_api_token = False
        self.auth = ""
        self.id = 0  # pylint: disable=invalid-name

        self.timeout = timeout

        if not server.endswith("/api_jsonrpc.php"):
            server = server.rstrip("/") + "/api_jsonrpc.php"
        self.url = server
        logger.info(f"JSON-RPC Server Endpoint: {self.url}")

        self.version: Optional[Version] = None
        self._detect_version = detect_version

    def __enter__(self) -> "ZabbixAPI":
        return self

    # pylint: disable=inconsistent-return-statements
    def __exit__(self, exception_type, exception_value, traceback):
        if isinstance(exception_value, (ZabbixAPIException, type(None))):
            if self.is_authenticated and not self.use_api_token:
                # Logout the user if they are authenticated using username + password.
                self.user.logout()
            return True
        return None

    def login(
        self,
        user: str = "",
        password: str = "",
        api_token: Optional[str] = None,
    ) -> None:
        """Convenience method for calling user.authenticate
        and storing the resulting auth token for further commands.

        If use_authenticate is set, it uses the older (Zabbix 1.8)
        authentication command

        :param password: Password used to login into Zabbix
        :param user: Username used to login into Zabbix
        :param api_token: API Token to authenticate with
        """

        if self._detect_version:
            self.version = Version(self.api_version())
            logger.info(f"Zabbix API version is: {self.version}")

        # If the API token is explicitly provided, use this instead.
        if api_token is not None:
            self.use_api_token = True
            self.auth = api_token
            return

        # If we have an invalid auth token, we are not allowed to send a login
        # request. Clear it before trying.
        self.auth = ""
        if self.use_authenticate:
            self.auth = self.user.authenticate(user=user, password=password)
        elif self.version and self.version >= ZABBIX_5_4_0:
            self.auth = self.user.login(username=user, password=password)
        else:
            self.auth = self.user.login(user=user, password=password)

    def check_authentication(self):
        if self.use_api_token:
            # We cannot use this call using an API Token
            return True
        # Convenience method for calling user.checkAuthentication of the current session
        return self.user.checkAuthentication(sessionid=self.auth)

    @property
    def is_authenticated(self) -> bool:
        if self.use_api_token:
            # We cannot use this call using an API Token
            return True

        try:
            self.user.checkAuthentication(sessionid=self.auth)
        except ZabbixAPIException:
            return False
        return True

    def confimport(
        self,
        confformat: str = "",
        source: str = "",
        rules: str = "",
    ) -> dict:
        """Alias for configuration.import because it clashes with
        Python's import reserved keyword
        :param rules:
        :param source:
        :param confformat:
        """
        warn(
            "ZabbixAPI.confimport(format, source, rules) has been deprecated, please use "
            "ZabbixAPI.configuration['import'](format=format, source=source, rules=rules) instead",
            DeprecationWarning,
            2,
        )

        return self.configuration["import"](
            format=confformat,
            source=source,
            rules=rules,
        )

    def api_version(self) -> str:
        return self.apiinfo.version()

    def do_request(
        self,
        method: str,
        params: Optional[Union[Mapping, Sequence]] = None,
    ) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.id,
        }
        headers = {}

        # We don't have to pass the auth token if asking for
        # the apiinfo.version or user.checkAuthentication
        anonymous_methods = {
            "apiinfo.version",
            "user.checkAuthentication",
            "user.login",
        }
        if self.auth and method not in anonymous_methods:
            if self.version and self.version >= ZABBIX_6_4_0:
                headers["Authorization"] = f"Bearer {self.auth}"
            else:
                payload["auth"] = self.auth

        logger.debug(f"Sending: {payload}")
        resp = self.session.post(
            self.url,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        logger.debug(f"Response Code: {resp.status_code}")

        # NOTE: Getting a 412 response code means the headers are not in the
        # list of allowed headers.
        resp.raise_for_status()

        if not resp.text:
            raise ZabbixAPIException("Received empty response")

        try:
            response = resp.json()
        except ValueError as exception:
            raise ZabbixAPIException(
                f"Unable to parse json: {resp.text}"
            ) from exception

        logger.debug(f"Response Body: {response}")

        self.id += 1

        if "error" in response:  # some exception
            error = response["error"]

            # some errors don't contain 'data': workaround for ZBX-9340
            if "data" not in error:
                error["data"] = "No data"

            raise ZabbixAPIException(
                f"Error {error['code']}: {error['message']}, {error['data']}",
                error["code"],
                error=error,
            )

        return response

    def _object(self, attr: str) -> "ZabbixAPIObject":
        """Dynamically create an object class (ie: host)"""
        return ZabbixAPIObject(attr, self)

    def __getattr__(self, attr: str) -> "ZabbixAPIObject":
        return self._object(attr)

    def __getitem__(self, attr: str) -> "ZabbixAPIObject":
        return self._object(attr)


# pylint: disable=too-few-public-methods
class ZabbixAPIMethod:
    def __init__(self, method: str, parent: ZabbixAPI):
        self._method = method
        self._parent = parent

    def __call__(self, *args, **kwargs):
        if args and kwargs:
            raise TypeError("Found both args and kwargs")

        return self._parent.do_request(self._method, args or kwargs)["result"]


# pylint: disable=too-few-public-methods
class ZabbixAPIObject:
    def __init__(self, name: str, parent: ZabbixAPI):
        self._name = name
        self._parent = parent

    def _method(self, attr: str) -> ZabbixAPIMethod:
        """Dynamically create a method (ie: get)"""
        return ZabbixAPIMethod(f"{self._name}.{attr}", self._parent)

    def __getattr__(self, attr: str) -> ZabbixAPIMethod:
        return self._method(attr)

    def __getitem__(self, attr: str) -> ZabbixAPIMethod:
        return self._method(attr)


class ZabbixAPIObjectClass(ZabbixAPIObject):
    def __init__(self, *args, **kwargs):
        warn(
            "ZabbixAPIObjectClass has been renamed to ZabbixAPIObject",
            DeprecationWarning,
            2,
        )
        super().__init__(*args, **kwargs)
