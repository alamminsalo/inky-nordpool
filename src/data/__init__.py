import os
import pandas as pd

from .spotprices import get_spotprices
from .fmi import get_fmidata

def collect_df():
    spotprices_file = '/tmp/spotprices.csv'
    if not os.path.isfile(spotprices_file):
        print("nordpool data: no data found, fetching...")
        df = get_spotprices()
        df.to_csv(spotprices_file, index=False)
    else:
        print("nordpool data: using cached csv")
        df = pd.read_csv(spotprices_file, parse_dates=['timestamp'])

    temp = get_fmidata(df.timestamp.min(), df.timestamp.max())
    df = df.set_index('timestamp').join(temp.set_index('timestamp')).reset_index()

    df['timestamp'] = df.timestamp.dt.tz_localize(None)
    df.set_index('timestamp', inplace=True)

    return df
