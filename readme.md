## Cloning the Repository

To clone this repository, run the following command in your terminal:

```bash
git clone https://github.com/lupoinvesting/DC_charts_loader.git
```

load the files you wish to browse in data folder

rename config_default.json to config.json

enter the name of the file you want to browse (not the _data.feather file) in config.json

## NEW: Dual Chart Grid Functionality 🆕

This repository now includes a powerful dual chart grid feature that allows you to display two charts side by side with advanced interaction capabilities.

### Features:
- **Side-by-side layout**: Two charts displayed horizontally
- **Maximize/minimize**: Click buttons to expand charts to full width
- **Timeframe switching**: Independent timeframe selection for each chart (1D, 4H, 1H, 15M, 5M, 1M)
- **Synchronized navigation**: Navigate both charts together
- **Dual screenshots**: Save screenshots of both charts simultaneously

### Quick Start:
```python
from src.models import ChartsDailyData
from src.ui import create_dual_chart_grid

# Load your data
chart_data = ChartsDailyData(dict_filename, data_filename)

# Create dual chart grid
dual_chart = create_dual_chart_grid(chart_data)
dual_chart.show(block=True)
```

### Demo:
```bash
python demo_dual_charts.py
```

For detailed documentation, see [DUAL_CHARTS_README.md](DUAL_CHARTS_README.md)

## CONTROLLING THE CHARTS
shift + 1 -> next chart
shift + 2 -> previous chart
shift + s -> screenshot


## TESTING
test with pytest:
```bash
python -m pytest --cov
```


# REFERENCE SITES
[tradingview lightweight charts](https://tradingview.github.io/lightweight-charts/docs)
[lightweight charts python](https://lightweight-charts-python.readthedocs.io/en/latest/index.html)

# GENERAL
activate environment from powershell
```bash
.\.venv\Scripts\Activate.ps1
```