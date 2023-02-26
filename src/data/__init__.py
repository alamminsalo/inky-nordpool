from .spotprices import get_spotprices
from .fmi import get_fmidata

def collect_df():
    df = get_spotprices()

    temp = get_fmidata(df.timestamp.min(), df.timestamp.max())
    df = df.set_index('timestamp').join(temp.set_index('timestamp')).reset_index()

    df['timestamp'] = df.timestamp.dt.tz_localize(None)
    df.set_index('timestamp', inplace=True)

    return df
