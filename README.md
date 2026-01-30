# AccessiSky

**Stay connected to what's above.**

[![CI](https://github.com/Orinks/AccessiSky/actions/workflows/ci.yml/badge.svg)](https://github.com/Orinks/AccessiSky/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
[![Built with wxPython](https://img.shields.io/badge/Built%20with-wxPython-blue)](https://wxpython.org/)

AccessiSky helps you stay aware of celestial events — whether or not you can see them. Built with full screen reader support, it brings ISS passes, moon phases, meteor showers, and more to everyone.

## Features

- **ISS Tracking**: Know when the International Space Station passes over your location
- **Moon Phases**: Current phase, illumination percentage, upcoming lunar events
- **Sun Data**: Sunrise, sunset, twilight times (civil, nautical, astronomical)
- **Aurora Forecast**: Kp index, geomagnetic activity, aurora visibility predictions
- **Space Weather**: Solar wind speed and density from NOAA SWPC
- **Meteor Showers**: Calendar of 11 major annual showers with peak dates, ZHR, and viewing ratings
- **Planet Visibility**: Which planets are visible tonight with rise/set estimates and brightness
- **Eclipse Calendar**: Solar and lunar eclipses from 2025-2030 with visibility regions
- **Viewing Conditions**: Combined score factoring clouds, moon, darkness, and light pollution
- **Dark Sky Times**: When true astronomical darkness begins/ends for astrophotography
- **Location Settings**: Save your coordinates for accurate calculations
- **Accessibility First**: Full screen reader support, keyboard navigation, proper labels

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

AccessiSky uses free, open APIs that require no API keys:

### Live API Data
- **[Open Notify](http://open-notify.org/)** - ISS current position and pass predictions
- **[Sunrise-Sunset.org](https://sunrise-sunset.org/api)** - Sun times and all twilight phases (civil, nautical, astronomical)
- **[NOAA SWPC](https://www.swpc.noaa.gov/)** - Space weather, Kp index, aurora forecasts
- **[USNO (US Naval Observatory)](https://aa.usno.navy.mil/data/api)** - Moon phases, illumination, rise/set times
- **[Open-Meteo](https://open-meteo.com/)** - Weather data for viewing conditions (cloud cover, visibility)

### Local Calculations (with API fallback)
- **Moon phases** - USNO API primary, local astronomical algorithms as fallback
- **Meteor showers** - IMO (International Meteor Organization) data, calculated locally
- **Planet visibility** - Simplified orbital mechanics, calculated locally
- **Eclipses** - NASA eclipse data for 2025-2030, stored locally
- **Viewing conditions** - Combines weather API data with local calculations

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
- `F1` - ISS Tracker tab
- `F2` - Moon Phases tab
- `F3` - Sun Times tab
- `F4` - Aurora Forecast tab
- `F5` - Meteor Showers tab
- `F6` - Planets tab
- `F7` - Eclipses tab
- `Ctrl+Tab` - Next tab
- `Ctrl+Q` - Quit

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [AccessiWeather](https://github.com/Orinks/AccessiWeather) - Accessible weather app (companion project)

## Development Setup

```bash
# Clone and install
git clone https://github.com/Orinks/AccessiSky.git
cd AccessiSky
pip install -e .[dev]

# Enable pre-push lint hook
git config core.hooksPath .githooks

# Or use pre-commit (alternative)
pip install pre-commit
pre-commit install
```

The pre-push hook runs `ruff check` before every push to catch lint errors early.
