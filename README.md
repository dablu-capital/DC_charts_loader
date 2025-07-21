# DC Charts Loader

A chart loading utility for data visualization.

## Installation

### With uv (recommended - linux)

First, install [uv](https://docs.astral.sh/uv/):

with Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

with Windows
```shell
pip install uv
```

```bash
uv sync
```

## Usage

Activate the virtual environment:

```bash
# With uv
uv shell
```

activate venv

# Or with traditional venv
```
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Development

To work on this project:

```bash
# Clone and setup
git clone <repository-url>
cd DC_charts_loader
uv sync

# Activate environment
uv shell
```