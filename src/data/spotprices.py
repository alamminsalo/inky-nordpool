import pandas as pd
from datetime import date, datetime, timedelta, timezone
from nordpool import elspot

def vat_fin() -> float:
    "Returns finnish VAT amount"
    if date.today() < date(2023,5,1):
        return 1.1
    return 1.24

def get_spotprices(currency: str = 'EUR', area: str = 'FI') -> pd.DataFrame:
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

if __name__ == '__main__':
    get_spotprices().to_csv('/tmp/spotprices.csv', index=False)
