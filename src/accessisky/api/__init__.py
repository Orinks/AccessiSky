"""API clients for AccessiSky."""

from .aurora import AuroraClient, AuroraForecast, GeomagActivity, KpIndex, SolarWind
from .briefing import (
    DailyBriefing,
    DailyBriefingData,
    SpaceWeatherSummary,
    generate_briefing_text,
)
from .darksky import (
    DarkSkyClient,
    DarkSkyWindow,
    TwilightType,
    get_dark_sky_window,
    get_darkness_duration,
    get_twilight_type,
    is_astronomical_darkness,
)
from .eclipses import (
    Eclipse,
    EclipseClient,
    EclipseInfo,
    EclipseType,
    get_all_eclipses,
    get_eclipse_info,
    get_next_eclipse,
    get_upcoming_eclipses,
)
from .geocoding import GeocodingClient, GeocodingResult, search_location
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
from .tonight import TonightData, TonightSummary, generate_summary_text
from .viewing import (
    CloudCover,
    ViewingClient,
    ViewingConditions,
    ViewingScore,
    calculate_viewing_score,
    get_moon_interference,
    get_viewing_conditions,
)
from .weather import (
    DailyWeather,
    HourlyWeather,
    WeatherClient,
    WeatherForecast,
)

__all__ = [
    # ISS
    "ISSClient",
    "ISSPosition",
    "ISSPass",
    # Dark Sky
    "DarkSkyClient",
    "DarkSkyWindow",
    "TwilightType",
    "get_dark_sky_window",
    "get_darkness_duration",
    "get_twilight_type",
    "is_astronomical_darkness",
    # Eclipses
    "Eclipse",
    "EclipseClient",
    "EclipseInfo",
    "EclipseType",
    "get_all_eclipses",
    "get_upcoming_eclipses",
    "get_eclipse_info",
    "get_next_eclipse",
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
    # Viewing Conditions
    "CloudCover",
    "ViewingClient",
    "ViewingConditions",
    "ViewingScore",
    "calculate_viewing_score",
    "get_moon_interference",
    "get_viewing_conditions",
    # Weather
    "WeatherClient",
    "WeatherForecast",
    "HourlyWeather",
    "DailyWeather",
    # Tonight's Summary
    "TonightData",
    "TonightSummary",
    "generate_summary_text",
    # Daily Briefing
    "DailyBriefing",
    "DailyBriefingData",
    "SpaceWeatherSummary",
    "generate_briefing_text",
    # Geocoding
    "GeocodingClient",
    "GeocodingResult",
    "search_location",
]
