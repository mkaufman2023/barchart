"""
## barchart.utils

Utility functions and classes.
"""
import requests
import threading
import urllib.parse
from typing import Optional


class BarchartSession(requests.Session):
    """
    A `requests.Session` subclass that fetches the XSRF cookie 
    from www.barchart.com and sets the X-Xsrf-Token header automatically.
    """
    def __init__(
            self,
            base_url: str = "https://www.barchart.com/",
            auto_init: bool = True,
            init_timeout: float = 10.0,
            auto_refresh_on_401: bool = True):
        """
        ## Parameters
            `base_url` - Where to GET to obtain XSRF cookie (defaults to https://www.barchart.com/).
            `auto_init` - If `True`, perform init during `__init__()`.
            `init_timeout` - Timeout in seconds for the initial `GET` request to fetch `XSRF` cookie.
            `auto_refresh_on_401` - If `True`, refresh token and retry once on 401/403.
        """
        super().__init__()
        self.base_url = base_url
        self._timeout = init_timeout
        self._auto_refresh_on_401 = auto_refresh_on_401
        
        self._initialized = False
        self._lock = threading.RLock()
        
        self.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        })
        
        if auto_init:
            self._init_xsrf()


    def _init_xsrf(self) -> str:
        """
        Makes a `GET` request so the server sets the `XSRF-TOKEN` cookie,
        then reads it and puts it in the session headers as `X-Xsrf-Token`.
        
        ## Returns
        - The XSRF token (unquoted).

        ## Raises
        - `RuntimeError` if the `XSRF-TOKEN` cookie is not present.
        """
        with self._lock:
            if self._initialized:
                return self.headers.get("X-Xsrf-Token", "")
            
            resp = super().get(self.base_url, timeout=self._timeout)
            resp.raise_for_status()

            raw_token: Optional[str] = self.cookies.get("XSRF-TOKEN")
            if not raw_token:
                raise RuntimeError("XSRF-TOKEN cookie not found after requesting {}".format(self.base_url))
            
            token = urllib.parse.unquote(raw_token)
            self.headers["X-Xsrf-Token"] = token
            self.headers.setdefault("Referer", self.base_url + "/")
            self._initialized = True
            return token


    def refresh_xsrf(self) -> str:
        """
        Forces a re-fetch of the `XSRF` token. Returns the new token.
        """
        with self._lock:
            self._initialized = False
            return self._init_xsrf()
        

    def request(self, method, url, **kwargs):
        """
        Override request to refresh token and retry on 401/403.
        """
        response = super().request(method, url, **kwargs)

        if self._auto_refresh_on_401 and response.status_code in (401, 403):
            with self._lock:
                try:
                    self.refresh_xsrf()
                except Exception:
                    return response
            return super().request(method, url, **kwargs)

        return response



# Create a default session instance
session = BarchartSession(auto_init=True, auto_refresh_on_401=True)

