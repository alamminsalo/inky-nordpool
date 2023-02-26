import pandas as pd
from datetime import datetime, timezone
from fmiopendata.wfs import download_stored_query

def get_fmidata(start_time, end_time):
    print("get_fmidata", start_time, end_time)

    forecast = download_stored_query(
        "fmi::forecast::harmonie::surface::point::multipointcoverage",
        [
            "starttime=" + start_time.tz_convert(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "endtime=" + end_time.tz_convert(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "place=Joensuu",
        ]
    )

    forecast = pd.DataFrame([
        dict(timestamp=key) |
        {key: value['value'] for key, value in point['Joensuu'].items()}
        for key, point in forecast.data.items()
    ])
    forecast['timestamp'] = pd.to_datetime(forecast.timestamp)
    forecast = forecast.set_index('timestamp')[['Air temperature']]

    now = datetime.now(timezone.utc)

    obs = download_stored_query(
        "fmi::observations::weather::hourly::multipointcoverage",
        [
            "starttime=" + min(now, start_time.tz_convert(timezone.utc)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "endtime=" + min(now, end_time.tz_convert(timezone.utc)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "place=Joensuu",
        ]
    )

    df = forecast

    if len(obs.data) > 0:
        obs = pd.DataFrame([
            dict(timestamp=key) |
            {key: value['value'] for key, value in point['Joensuu Linnunlahti'].items()}
            for key, point in obs.data.items()
        ])
        obs['timestamp'] = pd.to_datetime(obs.timestamp)
        obs = obs.set_index('timestamp')[['Air temperature']]

        df = pd.concat([obs, forecast.drop(obs.index)])

    # convert into same timezone with inputs
    df.reset_index(inplace=True)
    df['timestamp'] = df.reset_index().timestamp.dt.tz_localize(timezone.utc).dt.tz_convert(datetime.now().astimezone().tzinfo)

    return df
