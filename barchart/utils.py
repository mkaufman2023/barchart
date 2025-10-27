"""
## barchart.utils

Utility functions and classes.
"""
import requests
import datetime
import threading
import urllib.parse
from typing import Optional
from dataclasses import dataclass, field, asdict


def get_UOA_url(page: int) -> str:
    """
    Generates a URL for fetching unusual options activity data from Barchart.

    ### Parameters
    - `page` ( *int* ) - The page number for pagination.

    ### Returns
    - `str` - The complete URL for the API request.
    """
    # Check if today is Saturday or Sunday
    def is_weekend() -> bool:
        return datetime.datetime.now().weekday() in [5, 6]
    
    def is_saturday() -> bool:
        return datetime.datetime.now().weekday() == 5
    
    def is_sunday() -> bool:
        return datetime.datetime.now().weekday() == 6

    if is_weekend():
        # If today is Saturday, set start_date to yesterday
        if is_saturday():
            start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            end_date = start_date + datetime.timedelta(days=3)
        # If today is Sunday, set start_date to Friday
        elif is_sunday():
            start_date = datetime.datetime.now() - datetime.timedelta(days=2)
        # Set end_date to Monday
        end_date = start_date + datetime.timedelta(days=3)
    else:
        # If today is a weekday, set start_date to today and end_date to tomorrow
        start_date = datetime.datetime.now()
        end_date = start_date + datetime.timedelta(days=1)
    a = "https://www.barchart.com/proxies/core-api/v1/options/get?fields=symbol%2CbaseSymbol%2CbaseLastPrice%2CbaseSymbolType%2CexpirationDate%2CdaysToExpiration%2CsymbolType%2CstrikePrice%2ClastPrice%2Cmoneyness%2CbidPrice%2CaskPrice%2Cvolume%2CopenInterest%2CvolumeOpenInterestRatio%2CweightedImpliedVolatility%2Cdelta%2CtradeTime%2CsymbolCode&orderBy=volumeOpenInterestRatio&orderDir=desc&baseSymbolTypes=stock&between(volumeOpenInterestRatio%2C1.24%2C)=&between(lastPrice%2C.10%2C)=&between(tradeTime%2C"
    b = "%2C"
    c = ")=&between(volume%2C500%2C)=&between(openInterest%2C100%2C)=&in(exchange%2C(AMEX%2CNYSE%2CNASDAQ%2CINDEX-CBOE))=&meta=field.shortName%2Cfield.type%2Cfield.description&page="
    d = "&limit=300&raw=1"
    url = a + start_date.strftime("%Y-%m-%d") + b + end_date.strftime("%Y-%m-%d") + c + str(page) + d
    return url


@dataclass
class UOA_Entry:
    _raw: dict
    symbol: str = field(default="")                         # ["baseSymbol"]
    last_price: float = field(default=0.0)                  # ["raw"]["baseLastPrice"]
    expiration_date: str = field(default="")                # ["expirationDate"]
    days_to_expiration: int = field(default=0)              # ["raw"]["daysToExpiration"]
    option_type: str = field(default="")                    # ["symbolType"]
    strike_price: float = field(default=0.0)                # ["raw"]["strikePrice"]
    moneyness: float = field(default="")                    # ["raw"]["moneyness"]
    bid_price: float = field(default=0.0)                   # ["raw"]["bidPrice"]
    ask_price: float = field(default=0.0)                   # ["raw"]["askPrice"]
    volume: int = field(default=0)                          # ["raw"]["volume"]
    open_interest: int = field(default=0)                   # ["raw"]["openInterest"]
    volume_open_interest_ratio: float = field(default=0.0)  # ["raw"]["volumeOpenInterestRatio"]
    implied_volatility: float = field(default=0.0)          # ["raw"]["weightedImpliedVolatility"]
    delta: float = field(default=0.0)                       # ["raw"]["delta"]
    last_trade_time: int = field(default="")                # ["raw"]["tradeTime"]

    def __post_init__(self):
        """
        Post-initialization processing.
        """
        # Validate and set the raw data
        if not isinstance(self._raw, dict):
            raise ValueError("Raw data must be a dictionary")
        if not self._raw:
            raise ValueError("Raw data cannot be empty")
        # Set the attributes from the raw data
        self.symbol = self._raw.get("baseSymbol", "")
        self.last_price = self._raw.get("raw", {}).get("baseLastPrice", 0.0)
        self.expiration_date = self._raw.get("expirationDate", "")
        self.days_to_expiration = self._raw.get("raw", {}).get("daysToExpiration", 0)
        self.option_type = self._raw.get("symbolType", "")
        self.strike_price = self._raw.get("raw", {}).get("strikePrice", 0.0)
        self.moneyness = self._raw.get("raw", {}).get("moneyness", "")
        self.bid_price = self._raw.get("raw", {}).get("bidPrice", 0.0)
        self.ask_price = self._raw.get("raw", {}).get("askPrice", 0.0)
        self.volume = self._raw.get("raw", {}).get("volume", 0)
        self.open_interest = self._raw.get("raw", {}).get("openInterest", 0)
        self.volume_open_interest_ratio = self._raw.get("raw", {}).get("volumeOpenInterestRatio", 0.0)
        self.implied_volatility = self._raw.get("raw", {}).get("weightedImpliedVolatility", 0.0)
        self.delta = self._raw.get("raw", {}).get("delta", 0.0)
        self.last_trade_time = self._raw.get("raw", {}).get("tradeTime", "")

        # Convert expiration_date to a datetime object if it's not empty
        if self.expiration_date:
            try:
                # Format: MM/DD/YY
                self.expiration_date = datetime.datetime.strptime(self.expiration_date, "%m/%d/%y").date()
            except ValueError:
                raise ValueError(f"Invalid date format for expiration_date: {self.expiration_date}")
        # Convert last_trade_time to a datetime object if it's not empty
        if self.last_trade_time:
            try:
                # Format: 1748370476
                self.last_trade_time = datetime.datetime.fromtimestamp(self.last_trade_time)
            except ValueError:
                raise ValueError(f"Invalid date format for last_trade_time: {self.last_trade_time}")
        

    def to_dict(self) -> dict:
        """
        Convert the Entry instance to a dictionary.
        """
        d = asdict(self)
        d.pop('_raw', None)  # Remove the _raw field from the dictionary
        return d


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

