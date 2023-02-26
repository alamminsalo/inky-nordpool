import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from data import collect_df

plt.rcParams.update({
    'font.size': 8,
    'font.weight': 'bold',
})

# dictionary containing different dpi settings per display
dpi = dict(
    inky_what=120,
)

def render_figure(df: pd.DataFrame, width_px: int, height_px: int, dpi: int) -> Image:
    fig = plt.figure(
        figsize=(width_px/dpi, height_px/dpi), dpi=dpi
    )
    ax = fig.add_subplot(111)

    # main plot
    ax.step(
        df.index,
        df[df.columns[0]],
        color='black',
        linewidth=1,
        where='post',
    )

    # plot another column
    if len(df.columns) > 1:
        ax.twinx().plot(
            df.index,
            df[df.columns[1]],
            linestyle='--',
            color='black',
            linewidth=1,
        )

    # Show only hours in x axis
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H'))

    # Get current time, current value, min and max scalars
    current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    current_price, current_temp = df.query('index == @current_time').values[0]

    # Format row to string
    fmt = lambda x: f'{"{0:0.2f}".format(x)}'

    # Show current values as text
    ax.text(
        0.0, 1.0,
        f'Nyt: {fmt(current_price)} snt/kWh',
        horizontalalignment='left',
        verticalalignment='bottom',
        transform=ax.transAxes,
    )
    ax.text(
        1.0, 1.0,
        f'Lämpötila: {current_temp} °C',
        horizontalalignment='right',
        verticalalignment='bottom',
        transform=ax.transAxes,
    )
    # Arrow pointing to current value
    ax.annotate(
        " ",
        xy=(current_time + timedelta(minutes=30), current_price),
        horizontalalignment='center',
        arrowprops=dict(facecolor='black'),
    )

    fig.tight_layout()
    fig.canvas.draw()

    data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return Image.fromarray(data)

def update_display():
    # Get electricity prices, temperature as pandas dataframe
    df = collect_df()

    try:
        from inky.auto import auto
        display = auto()
    except:
        print('Cannot import inky. Skipping image rendering...')
        print(df)
        return

    # Render plot image using matplotlib and pillow
    img = render_figure(df, display.width, display.height, dpi['inky_what'])

    # Resize image to ensure its the correct display size and convert it to 1-bit black and white image.
    # Invert the values because the display shows black and white image in inverse.
    img = ImageOps.invert(img).resize(display.resolution).convert('P').convert('1')

    # Display image on screen
    display.set_image(img)
    display.show()

if __name__ == "__main__":
    update_display()
