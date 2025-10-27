"""
## barchart.options


"""


def get_unusual_activity(
        filters: dict = None,
        groupby_symbol: bool = False,
        groupby_optiontype: bool = False,
        groupby_expiration: bool = False,
    ) -> list[dict]:
    """
    Fetches "unusual options activity" data from Barchart.

    ### Parameters
    - `filters` ( *dict* ) - Optional filters to apply to the data. Possible keys include:
        - `symbol` - Filter by specific stock symbol(s).
        - `expiration_date` - Filter by expiration date.
        - `days_to_expiration` - Filter by days to expiration.
        - `option_type` - Filter by option type (e.g., "call", "put").
        - `volume` - Filter by volume.
        - `open_interest` - Filter by open interest.
        - `volume_open_interest_ratio` - Filter by volume/open interest ratio.
    - `groupby_symbol` ( *bool* ) - If `True`, groups the results by symbol instead of returning all entries as a flat list.
    - `groupby_optiontype` ( *bool* ) - If `True`, groups the results by option type instead of returning all entries as a flat list.
    - `groupby_expiration` ( *bool* ) - If `True`, groups the results by expiration date instead of returning all entries as a flat list.

    ### Returns
    - `list[dict]` - A list of dictionaries containing unusual options activity data.

    ### Formatting Examples for `filters`
    - `symbol`
        - `"symbol": lambda x: x["symbol"] == "RXRX"`           - Return only entries with symbol RXRX.
        - `"symbol": lambda x: x["symbol"] in ["RGTI", "QUBT"]` - Return only entries with symbol RGTI or QUBT.
    - `expiration_date`
        - `"expiration_date": lambda x: x["expiration_date"] > (datetime.now() + timedelta(days=30)).date()`  - Return only entries with expiration date more than 30 days from now.
        - `"expiration_date": lambda x: x["expiration_date"] < (datetime.now() + timedelta(days=30)).date()`  - Return only entries with expiration date less than 30 days from now.
    - `days_to_expiration`
        - `"days_to_expiration": lambda x: x["days_to_expiration"] < 45`                - Return only entries with less than 45 days to expiration.
        - `"days_to_expiration": lambda x: x["days_to_expiration"] > 45`                - Return only entries with more than 45 days to expiration.
    - `option_type`
        - `"option_type": lambda x: x["option_type"] == "Call"`                   - Return only entries with option type "Call".
        - `"option_type": lambda x: x["option_type"] == "Put"`                    - Return only entries with option type "Put".
    - `volume`
        - `"volume": lambda x: x["volume"] > 1000`                      - Return only entries with volume greater than 1,000 contracts.
        - `"volume": lambda x: x["volume"] < 1000`                      - Return only entries with volume less than 1,000 contracts.
    - `open_interest`
        - `"open_interest": lambda x: x["open_interest"] > 500`                - Return only entries with open interest greater than 500 contracts.
        - `"open_interest": lambda x: x["open_interest"] < 500`                - Return only entries with open interest less than 500 contracts.
    - `volume_open_interest_ratio`
        - `"volume_open_interest_ratio": lambda x: x["volume_open_interest_ratio"] > 1.5`   - Return only entries with a volume/open interest ratio greater than 1.5.
        - `"volume_open_interest_ratio": lambda x: x["volume_open_interest_ratio"] < 1.5`   - Return only entries with a volume/open interest ratio less than 1.5.
    """
    from .utils import get_UOA_url, UOA_Entry, session
    
    ua = []
    url = get_UOA_url(1)
    response = session.get(url)
    if response.status_code != 200:
        response.raise_for_status()
    # print(url)
    # print(response.json())
    data: dict = response.json()
    if not data.get("data"):
        raise ValueError("No data was found in the response.")
    ua.extend(data["data"])
    total = int(data["total"])
    # print(f"> Total unusual options activity records: {total}")
    remaining = total - 300
    if remaining > 0:
        num_pages = remaining // 300 + 1
        for page in range(2, num_pages + 2):
            url = get_UOA_url(page)
            response = session.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            data = response.json()
            if not data.get("data"):
                break
            ua.extend(data["data"])
    alldata = dict(
        data   = ua,
        total  = total,
        fields = data["meta"]["field"],
    )
    entries = [UOA_Entry(item) for item in alldata["data"]]
    entries_dicts = [entry.to_dict() for entry in entries]
    if filters:
        filtered_activity = [entry for entry in entries_dicts if all(f(entry) for f in filters.values())]
        entries_dicts = filtered_activity
    if groupby_symbol:
        grouped_activity = {}
        for entry in entries_dicts:
            symbol = entry["symbol"]
            if symbol not in grouped_activity:
                grouped_activity[symbol] = []
            grouped_activity[symbol].append(entry)
        entries_dicts = grouped_activity
        if groupby_optiontype:
            for symbol, entries in entries_dicts.items():
                grouped_by_optiontype = {}
                for entry in entries:
                    option_type = entry["option_type"]
                    if option_type not in grouped_by_optiontype:
                        grouped_by_optiontype[option_type] = []
                    grouped_by_optiontype[option_type].append(entry)
                entries_dicts[symbol] = grouped_by_optiontype
    if groupby_optiontype and not groupby_symbol:
        grouped_activity = {}
        for entry in entries_dicts:
            option_type = entry["option_type"]
            if option_type not in grouped_activity:
                grouped_activity[option_type] = []
            grouped_activity[option_type].append(entry)
        entries_dicts = grouped_activity
    if groupby_expiration and not (groupby_symbol or groupby_optiontype):
        grouped_activity = {}
        for entry in entries_dicts:
            expiration_date = entry["expiration_date"]
            if expiration_date not in grouped_activity:
                grouped_activity[expiration_date] = []
            grouped_activity[expiration_date].append(entry)
        entries_dicts = grouped_activity
    if groupby_expiration and groupby_optiontype and not groupby_symbol:
        grouped_activity = {}
        for entry in entries_dicts:
            option_type = entry["option_type"]
            expiration_date = entry["expiration_date"]
            if option_type not in grouped_activity:
                grouped_activity[option_type] = {}
            if expiration_date not in grouped_activity[option_type]:
                grouped_activity[option_type][expiration_date] = []
            grouped_activity[option_type][expiration_date].append(entry)
        # Sort the expiration date keys in each option type by date
        for option_type, expirations in grouped_activity.items():
            sorted_expirations = dict(sorted(expirations.items(), key=lambda x: x[0]))
            grouped_activity[option_type] = sorted_expirations
        entries_dicts = grouped_activity
    if groupby_expiration and groupby_symbol and not groupby_optiontype:
        grouped_activity = {}
        for entry in entries_dicts:
            symbol = entry["symbol"]
            expiration_date = entry["expiration_date"]
            if symbol not in grouped_activity:
                grouped_activity[symbol] = {}
            if expiration_date not in grouped_activity[symbol]:
                grouped_activity[symbol][expiration_date] = []
            grouped_activity[symbol][expiration_date].append(entry)
        # Sort the expiration date keys in each symbol by date
        for symbol, expirations in grouped_activity.items():
            sorted_expirations = dict(sorted(expirations.items(), key=lambda x: x[0]))
            grouped_activity[symbol] = sorted_expirations
        entries_dicts = grouped_activity
    if groupby_symbol and groupby_optiontype and groupby_expiration:
        grouped_activity = {}
        for symbol, values in entries_dicts.items():
            for option_type, entries in values.items():
                for entry in entries:
                    expiration_date = entry["expiration_date"]
                    if symbol not in grouped_activity:
                        grouped_activity[symbol] = {}
                    if option_type not in grouped_activity[symbol]:
                        grouped_activity[symbol][option_type] = {}
                    if expiration_date not in grouped_activity[symbol][option_type]:
                        grouped_activity[symbol][option_type][expiration_date] = []
                    grouped_activity[symbol][option_type][expiration_date].append(entry)
        # Sort the expiration date keys in each symbol and option type by date
        for symbol, option_types in grouped_activity.items():
            for option_type, expirations in option_types.items():
                sorted_expirations = dict(sorted(expirations.items(), key=lambda x: x[0]))
                grouped_activity[symbol][option_type] = sorted_expirations
        entries_dicts = grouped_activity

    return entries_dicts


def get_most_active() -> list[dict]:
    """
    Fetches "most active options" data from Barchart.

    ### Returns
    - `list[dict]` - A list of dictionaries containing most active options data.
    """
    from .utils import get_MAO_url, session
    
    mao = []
    url = get_MAO_url(1)
    response = session.get(url)
    if response.status_code != 200:
        response.raise_for_status()
    # print(url)
    # print(response.json())
    data: dict = response.json()
    if not data.get("data"):
        raise ValueError("No data was found in the response.")
    mao.extend(data["data"])
    total = int(data["total"])
    print(f"> Total 'most active options' records: {total}")
    remaining = total - 300
    if remaining > 0:
        num_pages = remaining // 300 + 1
        for page in range(2, num_pages + 2):
            url = get_MAO_url(page)
            response = session.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            data = response.json()
            if not data.get("data"):
                break
            mao.extend(data["data"])
    alldata = dict(
        data   = mao,
        total  = total,
        fields = data["meta"]["field"],
    )
    data = alldata["data"]
    return [item["raw"] for item in data]


def get_top_covered_call_ideas() -> list[dict]:
    """
    Fetches "top covered call ideas" data from Barchart.

    ### Returns
    - `list[dict]` - A list of dictionaries containing top covered call ideas data.
    """
    from .utils import get_TCCI_url, session
    
    tcci = []
    url = get_TCCI_url(1)
    response = session.get(url)
    if response.status_code != 200:
        response.raise_for_status()
    # print(url)
    # print(response.json())
    data: dict = response.json()
    if not data.get("data"):
        raise ValueError("No data was found in the response.")
    tcci.extend(data["data"])
    total = int(data["total"])
    print(f"> Total 'most active options' records: {total}")
    remaining = total - 300
    if remaining > 0:
        num_pages = remaining // 300 + 1
        for page in range(2, num_pages + 2):
            url = get_TCCI_url(page)
            response = session.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            data = response.json()
            if not data.get("data"):
                break
            tcci.extend(data["data"])
    alldata = dict(
        data   = tcci,
        total  = total,
        fields = data["meta"]["field"],
    )
    return alldata
    # data = alldata["data"]
    # return [item["raw"] for item in data]

