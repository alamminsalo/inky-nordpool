import pandas as pd
from datetime import date, datetime, timedelta, timezone

def vat_fin() -> float:
    "Returns finnish VAT amount"
    if date.today() < date(2023,5,1):
        return 1.1
    return 1.24

def get_spotprices(currency: str, area: str) -> pd.DataFrame:
    from nordpool import elspot
    prices_spot = elspot.Prices(currency=currency)
    prices_today = prices_spot.hourly(end_date=date.today(), areas=[area])['areas'][area]['values']
    df = pd.DataFrame(prices_today)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    # When current time is past 6pm,
    # also fetch next day and slice the next 24-hour period
    if now.hour >= 18:
        prices_tomorrow = prices_spot.hourly(end_date=date.today() + timedelta(days=1), areas=[area])['areas'][area]['values']
        df = pd.concat([df, pd.DataFrame(prices_tomorrow)], ignore_index=True).iloc[18:]

    # Convert dates to local timezone
    df['timestamp'] = df['start'].dt.tz_convert(now.astimezone().tzinfo)#.dt.tz_localize(None)

    # Convert price to cents/KWh and add VAT
    df['price'] = df.value * 0.1 * vat_fin()

    return df[['timestamp','price']]

def get_fmidata(start_time, end_time):
    from fmiopendata.wfs import download_stored_query

    obs = download_stored_query(
        "fmi::observations::weather::hourly::multipointcoverage",
        [
            "starttime=" + start_time.tz_convert(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "endtime=" + end_time.tz_convert(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "place=Joensuu",
        ]
    )

    obs = pd.DataFrame([
        dict(timestamp=key) |
        {key: value['value'] for key, value in point['Joensuu Linnunlahti'].items()}
        for key, point in obs.data.items()
    ])
    obs['timestamp'] = pd.to_datetime(obs.timestamp)#.dt.tz_localize(timezone.utc).dt.tz_convert(datetime.now().astimezone().tzinfo).dt.tz_localize(None)
    obs = obs.set_index('timestamp')[['Air temperature']]

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
    forecast['timestamp'] = pd.to_datetime(forecast.timestamp)#.dt.tz_localize(timezone.utc).dt.tz_convert(start_time.astimezone().tzinfo).dt.tz_localize(None)
    forecast = forecast.set_index('timestamp')[['Air temperature']]

    df = pd.concat([obs, forecast.drop(obs.index)])

    # convert into same timezone with inputs
    df.reset_index(inplace=True)
    df['timestamp'] = df.reset_index().timestamp.dt.tz_localize(timezone.utc).dt.tz_convert(datetime.now().astimezone().tzinfo)

    return df

def collect_df():
    df = get_spotprices('EUR','FI')

    temp = get_fmidata(df.timestamp.min(), df.timestamp.max())
    df = df.set_index('timestamp').join(temp.set_index('timestamp')).reset_index()

    df['timestamp'] = df.timestamp.dt.tz_localize(None)

    return df.set_index('timestamp')

if __name__ == '__main__':
    collect_df().to_csv('data.csv')
