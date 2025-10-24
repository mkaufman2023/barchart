"""
## barchart.stocks


"""

def test():
    """
    ## barchart.stocks.test
    """
    from .utils import session

    r = session.get("https://www.barchart.com/proxies/core-api/v1/quotes/get?lists=etfs.us.price_volume.advances.overall&orderDir=desc&fields=symbol%2CsymbolName%2ClastPrice%2CpriceChange%2CpercentChange%2ChighPrice%2ClowPrice%2Cvolume%2CpriceVolume%2CtradeTime%2CsymbolCode%2CsymbolType%2ChasOptions&orderBy=priceVolume&meta=field.shortName%2Cfield.type%2Cfield.description%2Clists.lastUpdate&hasOptions=true&raw=1")
    r.raise_for_status()
    data = r.json()

    print(f"stocks.test: {str(data)[:20]}")

