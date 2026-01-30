# Changelog

All notable changes to AccessiSky will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Tonight's summary feature (in progress)
- Daily briefing (in progress)

## [0.2.0] - 2026-01-30

### Added
- **Meteor Shower Calendar**: 11 major annual showers with peak dates, ZHR, viewing ratings
- **Planet Visibility**: Track all 7 observable planets with visibility status
- **Eclipse Calendar**: Solar and lunar eclipses from 2025-2030
- **Dark Sky Times**: Astronomical twilight calculations for astrophotography
- **Viewing Conditions Score**: Combined rating (0-100) factoring clouds, moon, darkness
- **Weather Integration**: Open-Meteo API for cloud cover and visibility
- **USNO Moon API**: Accurate moon data from US Naval Observatory
- Pre-push git hook for automatic linting

### Changed
- Moon phases now use USNO API with local calculation fallback
- Viewing conditions integrate real weather data

## [0.1.0] - 2026-01-30

### Added
- Initial release
- **ISS Tracking**: Current position and pass predictions
- **Moon Phases**: Phase name, illumination, rise/set times
- **Sun Times**: Sunrise, sunset, civil/nautical/astronomical twilight
- **Aurora Forecast**: Kp index and geomagnetic activity from NOAA SWPC
- **Location Management**: Set location with coordinates or city presets
- Accessible UI with full screen reader support
- Keyboard navigation (F1-F7 for tabs, standard shortcuts)
- GitHub Actions CI pipeline

### Technical
- wxPython-based cross-platform GUI
- Free APIs only (no API keys required)
- 144 passing tests

[Unreleased]: https://github.com/Orinks/AccessiSky/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Orinks/AccessiSky/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Orinks/AccessiSky/releases/tag/v0.1.0
