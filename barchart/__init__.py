"""
## barchart


"""
from . import etfs, options, stocks

try:
    from importlib.metadata import version
    __version__ = version("barchart")
except Exception:
    __version__ = "0.0.0"