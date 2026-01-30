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
    # Aurora
    "AuroraClient",
    "AuroraForecast",
    "KpIndex",
    "SolarWind",
    "GeomagActivity",
]
