from src.models import ChartsDailyData
from src.ui import create_and_bind_chart, create_dual_chart_grid
from src.config import config
from pathlib import Path

if __name__ == "__main__":

    path = Path.cwd() / config.general.data_path
    filename = config.general.data_filename
    dict_filename = path / filename
    # dict_filename =
    data_filename = dict_filename.with_name(dict_filename.stem + "_data.feather")
    chart_data = ChartsDailyData(dict_filename, data_filename)

    # Choose between single chart or dual chart grid
    use_dual_chart = config.chart.use_intraday_tf  # Set to False for single chart

    if use_dual_chart:
        chart = create_dual_chart_grid(chart_data)
    else:
        chart = create_and_bind_chart(chart_data)

    chart.show(block=True)
