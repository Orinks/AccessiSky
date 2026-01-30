"""API clients for AccessiSky."""

from .aurora import AuroraClient, AuroraForecast, GeomagActivity, KpIndex, SolarWind
from .iss import ISSClient, ISSPass, ISSPosition
from .meteors import (
    MeteorClient,
    MeteorShower,
    MeteorShowerInfo,
    get_active_showers,
    get_all_showers,
    get_shower_info,
    get_upcoming_showers,
)
from .moon import (
    MoonClient,
    MoonEvent,
    MoonInfo,
    MoonPhase,
    get_moon_info,
    get_moon_phase,
    get_upcoming_events,
)
from .planets import (
    Planet,
    PlanetClient,
    PlanetInfo,
    PlanetVisibility,
    get_all_planets,
    get_planet_info,
    get_visible_planets,
)
from .sun import SunClient, SunTimes

__all__ = [
    # ISS
    "ISSClient",
    "ISSPosition",
    "ISSPass",
    # Sun
    "SunClient",
    "SunTimes",
    # Moon
    "MoonClient",
    "MoonInfo",
    "MoonEvent",
    "MoonPhase",
    "get_moon_info",
    "get_moon_phase",
    "get_upcoming_events",
    # Meteors
    "MeteorClient",
    "MeteorShower",
    "MeteorShowerInfo",
    "get_all_showers",
    "get_upcoming_showers",
    "get_active_showers",
    "get_shower_info",
    # Planets
    "Planet",
    "PlanetClient",
    "PlanetInfo",
    "PlanetVisibility",
    "get_all_planets",
    "get_visible_planets",
    "get_planet_info",
    # Aurora
    "AuroraClient",
    "AuroraForecast",
    "KpIndex",
    "SolarWind",
    "GeomagActivity",
]
