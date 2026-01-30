# AccessiSky

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
[![Built with wxPython](https://img.shields.io/badge/Built%20with-wxPython-blue)](https://wxpython.org/)

AccessiSky is an accessible sky tracking application built with Python and wxPython. Track ISS passes, satellite visibility, moon phases, and more with full screen reader support.

## Features

- **ISS Tracking**: Know when the International Space Station passes over your location
- **Satellite Passes**: Track visible satellite passes in your area
- **Moon Phases**: Current phase, next full moon, next new moon
- **Sun Data**: Sunrise, sunset, twilight times
- **Meteor Showers**: Upcoming meteor shower predictions
- **Aurora Forecast**: Geomagnetic activity and aurora visibility
- **Accessibility First**: Full screen reader support, keyboard navigation, ARIA labels

## Installation

```bash
# Clone the repository
git clone https://github.com/Orinks/AccessiSky.git
cd AccessiSky

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run the app
python -m accessisky
```

## Data Sources

AccessiSky uses free, open APIs:

- **Open Notify** - ISS current position and pass predictions
- **CelesTrak** - Satellite TLE data
- **Sunrise-Sunset.org** - Sun times
- **Open-Meteo** - Weather conditions for visibility
- **SWPC/NOAA** - Space weather and aurora forecasts

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/accessisky --cov-report=term-missing

# Lint code
ruff check .

# Format code
ruff format .
```

## Keyboard Shortcuts

- `Ctrl+R` - Refresh all data
- `Ctrl+L` - Set location
- `Ctrl+,` - Settings
- `F5` - Refresh current view
- `Ctrl+Q` - Quit

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [AccessiWeather](https://github.com/Orinks/AccessiWeather) - Accessible weather app (companion project)
