import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nordpool import elspot
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta

INKYWHAT_DPI=120

def vat_fin() -> float:
    "Returns finnish VAT amount"
    if date.today() < date(2023,5,1):
        return 1.1
    return 1.24

def get_spotprices() -> pd.DataFrame:
    prices_spot = elspot.Prices()
    end_date = date.today()# + timedelta(days=1)
    prices = prices_spot.hourly(end_date=end_date, areas=['FI'])
    df = pd.DataFrame(prices['areas']['FI']['values'])
    df['start'] = df['start'].dt.tz_convert('Europe/Helsinki')
    df['end'] = df['end'].dt.tz_convert('Europe/Helsinki')
    # Convert price to EUR/KWh and add VAT
    df['value'] *= 0.001 * vat_fin()
    df['cents_kwh'] = df['value'] * 100
    df['hour'] = df.start.dt.strftime('%H')
    return df

def pricesfig(prices: pd.DataFrame, dpi: int = INKYWHAT_DPI) -> Image:
    plt.rcParams.update({
        'font.size': 9,
       # 'font.family': 'monospace',
        'font.weight': 'bold',
    })
    fig = plt.figure(
        figsize=(400/dpi, 300/dpi), dpi=dpi
    )
    ax = fig.add_subplot(111)
    ax.plot(
        df.hour,
        df.cents_kwh,
        'black',
    )
    plt.xticks(df[df.index % 2 != 0].hour)

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

def inky_draw(img: Image):
    from inky.auto import auto
    display = auto()
    img = ImageOps.invert(img).resize(display.resolution).convert('P').convert('1')
    display.set_image(img)
    display.show()

if __name__ == "__main__":
    df = get_spotprices()
    img = pricesfig(df)
    inky_draw(img)
