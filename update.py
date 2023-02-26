import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nordpool import elspot
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
import argparse

# dictionary containing different dpi settings per display
dpi = dict(
    inky_what=120,
)

def vat_fin() -> float:
    "Returns finnish VAT amount"
    if date.today() < date(2023,5,1):
        return 1.1
    return 1.24

def get_spotprices(currency: str, area: str) -> pd.DataFrame:
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
    df['start'] = df['start'].dt.tz_convert(now.astimezone().tzinfo).dt.tz_localize(None)
    df['end'] = df['end'].dt.tz_convert(now.astimezone().tzinfo).dt.tz_localize(None)

    # Current time marker
    df['current'] = df.start == now

    # Convert price to cents/KWh and add VAT
    df['value'] *= 0.1 * vat_fin()

    return df

def pricesfig(prices: pd.DataFrame, width_px: int, height_px: int, dpi: int) -> Image:
    plt.rcParams.update({
        'font.size': 8,
        'font.weight': 'bold',
    })
    fig = plt.figure(
        figsize=(width_px/dpi, height_px/dpi), dpi=dpi
    )
    ax = fig.add_subplot(111)

    ax.plot(
        prices.start.dt.tz_localize(None),
        prices.value,
        color='black',
        linewidth=1,
    )
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H'))

    # Get current time, current value, min and max scalars
    current_time, current_value = prices.query('current')[['start','value']].values[0]
    min_value=prices['value'].min()
    max_value=prices['value'].max()

    # Value formatter
    fmt = lambda x: f'{"{0:0.2f}".format(x)}'

    # Arrow pointing to current value
    ax.annotate(
        " ",
        xy=(current_time, current_value),
        horizontalalignment='center',
        arrowprops=dict(facecolor='black'),
    )
    # Current value textbox
    ax.text(
        0, 1.0,
        f'Nyt: {fmt(current_value)} snt/kWh',
        horizontalalignment='left',
        verticalalignment='bottom',
        transform=ax.transAxes,
        bbox=dict(
            boxstyle='square',
            facecolor='white',
        ),

    )
    # Min, max values text
    ax.text(
        1.0, 1.0,
        f'Min: {fmt(min_value)} Max: {fmt(max_value)}',
        horizontalalignment='right',
        verticalalignment='bottom',
        transform=ax.transAxes
    )
    fig.tight_layout()
    fig.canvas.draw()

    data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return Image.fromarray(data)

def update_display(currency: str, area: str):
    from inky.auto import auto
    display = auto()

    # Get electricity prices as pandas dataframe
    df = get_spotprices(currency, area)

    # Render plot image using matplotlib and pillow
    img = pricesfig(df, display.width, display.height, dpi['inky_what'])

    # Resize image to ensure its the correct display size and convert it to 1-bit black and white image.
    # Invert the values because the display shows black and white image in inverse.
    img = ImageOps.invert(img).resize(display.resolution).convert('P').convert('1')

    # Display image on screen
    display.set_image(img)
    display.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = 'inky-nordpool.update', description = 'Fetches nordpool data and displays it on inky eink display')
    parser.add_argument('-c', '--currency', default='EUR')
    parser.add_argument('-a', '--area', default='FI')
    args = parser.parse_args()

    update_display(args.currency, args.area)
