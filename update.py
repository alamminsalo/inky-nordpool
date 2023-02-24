import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nordpool import elspot
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta

# dictionary containing different dpi settings per display
dpi = dict(
    inky_what=120,
)

def vat_fin() -> float:
    "Returns finnish VAT amount"
    if date.today() < date(2023,5,1):
        return 1.1
    return 1.24

def get_spotprices() -> pd.DataFrame:
    prices_spot = elspot.Prices()

    prices_today = prices_spot.hourly(end_date=date.today(), areas=['FI'])['areas']['FI']['values']
    df = pd.DataFrame(prices_today)

    # when current time is past 6pm,
    # also fetch next day and slice the middle 24-hour period
    if datetime.now().hour >= 18:
        prices_tomorrow = prices_spot.hourly(areas=['FI'])['areas']['FI']['values']
        df = pd.concat([df, pd.DataFrame(prices_tomorrow)], ignore_index=True).iloc[12:36]

    df['start'] = df['start'].dt.tz_convert('Europe/Helsinki')
    df['end'] = df['end'].dt.tz_convert('Europe/Helsinki')

    # Convert price to EUR/KWh and add VAT
    df['value'] *= 0.001 * vat_fin()
    df['cents_kwh'] = df['value'] * 100
    df['hour'] = df.start.dt.strftime('%H')
    return df

def pricesfig(prices: pd.DataFrame, width_px: int, height_px: int, dpi: int) -> Image:
    plt.rcParams.update({
        'font.size': 9,
       # 'font.family': 'monospace',
        'font.weight': 'bold',
    })
    fig = plt.figure(
        figsize=(width_px/dpi, height_px/dpi), dpi=dpi
    )
    ax = fig.add_subplot(111)
    ax.plot(
        prices.hour,
        prices.cents_kwh,
        'black',
    )
    plt.xticks(prices[prices.index % 2 != 0].hour)

    # If not starting from the first hour draw vertical line to midnight
    if prices.hour.values[0] != "00":
        ax.axvline("00")

    current_hour = datetime.now().strftime('%H')
    current_value = prices.query('hour == @current_hour')['cents_kwh'].values[0]

    min_value=prices['cents_kwh'].min()
    max_value=prices['cents_kwh'].max()

    fmt = lambda x: f'{"{0:0.2f}".format(x)}'

    # arrow pointing to current value
    ax.annotate(
        " ",
        xy=(current_hour, current_value),
        horizontalalignment='center',
        arrowprops=dict(facecolor='black'),
    )
    ax.text(
        0, 1.0,
        f'Nyt: {fmt(current_value)}',
        horizontalalignment='left',
        verticalalignment='bottom',
        transform=ax.transAxes,
        bbox=dict(
            boxstyle='square',
            facecolor='white',
        ),
        fontsize=10,
    )
    ax.text(
        1.0, 1.0,
        f'Min: {fmt(min_value)} Max: {fmt(max_value)}',
        horizontalalignment='right',
        verticalalignment='bottom',
        transform=ax.transAxes
    )
    fig.canvas.draw()

    data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return Image.fromarray(data)

def update_display():
    from inky.auto import auto
    display = auto()

    # Get electricity prices as pandas dataframe
    df = get_spotprices()

    # Render plot image using matplotlib and pillow
    img = pricesfig(df, display.width, display.height, dpi['inky_what'])

    # Resize image to ensure its the correct display size and convert it to 1-bit black and white image.
    # Invert the values because the display shows black and white image in inverse.
    img = ImageOps.invert(img).resize(display.resolution).convert('P').convert('1')

    # Display image on screen
    display.set_image(img)
    display.show()

if __name__ == "__main__":
    update_display()
