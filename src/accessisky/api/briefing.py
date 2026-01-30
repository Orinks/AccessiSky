"""Daily Briefing API - summary of sky events for the entire day.

Provides a comprehensive overview of what's happening in the sky today,
including sunrise/sunset, moon data, ISS passes (day and night),
planetary positions, meteor showers, eclipses, and space weather.

Designed for programmatic access (external tools, cron jobs) and
accessibility (plain-language summaries for screen readers).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class SpaceWeatherSummary:
    """Summary of space weather conditions."""

    kp_current: float | None = None
    kp_24h_max: float | None = None
    activity_level: str | None = None  # "Quiet", "Unsettled", "Minor Storm", etc.
    solar_wind_speed: float | None = None  # km/s
    aurora_visibility: str | None = None  # Description of where aurora may be visible

    def __str__(self) -> str:
        if self.kp_current is None:
            return "Space weather data unavailable"

        parts = [f"Kp {self.kp_current:.1f}"]
        if self.activity_level:
            parts.append(f"({self.activity_level})")
        if self.solar_wind_speed:
            parts.append(f", solar wind {self.solar_wind_speed:.0f} km/s")

        return "".join(parts)


@dataclass
class DailyBriefingData:
    """Aggregated data for a daily sky briefing."""

    # Date
    date: date | None = None

    # Sun data
    sunrise: str | None = None  # Time string (HH:MM)
    sunset: str | None = None
    day_length: str | None = None  # "Xh Ym"

    # Moon data
    moon_phase: str | None = None
    moon_illumination: int | None = None  # 0-100
    moon_rise: str | None = None
    moon_set: str | None = None

    # ISS passes (all passes, day and night)
    iss_passes: list[str] = field(default_factory=list)

    # Visible planets
    visible_planets: list[str] = field(default_factory=list)

    # Meteor showers
    active_meteor_showers: list[str] = field(default_factory=list)

    # Eclipse (if any today)
    eclipse_today: str | None = None

    # Space weather
    space_weather: SpaceWeatherSummary | None = None

    # Generated summary
    summary_text: str | None = None

    def as_dict(self) -> dict:
        """Export briefing data as a dictionary for programmatic use."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "sun": {
                "sunrise": self.sunrise,
                "sunset": self.sunset,
                "day_length": self.day_length,
            },
            "moon": {
                "phase": self.moon_phase,
                "illumination": self.moon_illumination,
                "rise": self.moon_rise,
                "set": self.moon_set,
            },
            "iss_passes": self.iss_passes,
            "planets": self.visible_planets,
            "meteor_showers": self.active_meteor_showers,
            "eclipse": self.eclipse_today,
            "space_weather": {
                "kp_current": self.space_weather.kp_current if self.space_weather else None,
                "kp_24h_max": self.space_weather.kp_24h_max if self.space_weather else None,
                "activity": self.space_weather.activity_level if self.space_weather else None,
                "solar_wind_speed": (
                    self.space_weather.solar_wind_speed if self.space_weather else None
                ),
                "aurora_visibility": (
                    self.space_weather.aurora_visibility if self.space_weather else None
                ),
            },
            "summary": self.summary_text,
        }


def generate_briefing_text(data: DailyBriefingData) -> str:
    """
    Generate a human-readable daily briefing from DailyBriefingData.

    Creates a natural language description suitable for screen readers
    and external tools like morning briefing systems.

    Args:
        data: DailyBriefingData with aggregated sky information

    Returns:
        Plain-language briefing string
    """
    parts = []

    # Date header
    if data.date:
        date_str = data.date.strftime("%B %d, %Y")
        parts.append(f"Sky Briefing for {date_str}:")
    else:
        parts.append("Daily Sky Briefing:")

    # Sun times
    if data.sunrise and data.sunset:
        sun_str = f"Sunrise at {data.sunrise}, sunset at {data.sunset}"
        if data.day_length:
            sun_str += f" ({data.day_length} of daylight)"
        parts.append(sun_str + ".")
    elif data.sunrise:
        parts.append(f"Sunrise at {data.sunrise}.")
    elif data.sunset:
        parts.append(f"Sunset at {data.sunset}.")

    # Moon info
    if data.moon_phase:
        moon_str = f"Moon: {data.moon_phase}"
        if data.moon_illumination is not None:
            moon_str += f" ({data.moon_illumination}% illuminated)"
        moon_times = []
        if data.moon_rise:
            moon_times.append(f"rises {data.moon_rise}")
        if data.moon_set:
            moon_times.append(f"sets {data.moon_set}")
        if moon_times:
            moon_str += ", " + " and ".join(moon_times)
        parts.append(moon_str + ".")

    # Eclipse alert (important - put near top)
    if data.eclipse_today:
        parts.append(f"⚠️ Eclipse today: {data.eclipse_today}")

    # ISS passes
    if data.iss_passes:
        if len(data.iss_passes) == 1:
            parts.append(f"ISS pass: {data.iss_passes[0]}.")
        else:
            parts.append(f"ISS has {len(data.iss_passes)} passes today:")
            for pass_info in data.iss_passes[:4]:  # Limit to 4
                parts.append(f"  • {pass_info}")

    # Visible planets
    if data.visible_planets:
        if len(data.visible_planets) == 1:
            parts.append(f"{data.visible_planets[0]} is visible today.")
        elif len(data.visible_planets) == 2:
            parts.append(f"{data.visible_planets[0]} and {data.visible_planets[1]} are visible.")
        else:
            planet_list = ", ".join(data.visible_planets[:-1])
            planet_list += f", and {data.visible_planets[-1]}"
            parts.append(f"Visible planets: {planet_list}.")

    # Meteor showers
    if data.active_meteor_showers:
        if len(data.active_meteor_showers) == 1:
            parts.append(f"The {data.active_meteor_showers[0]} meteor shower is active.")
        else:
            showers = " and ".join(data.active_meteor_showers[:2])
            parts.append(f"Active meteor showers: {showers}.")

    # Space weather
    if data.space_weather:
        sw = data.space_weather
        if sw.kp_current is not None:
            if sw.kp_current >= 5:
                # Storm conditions - important!
                activity = sw.activity_level or "elevated"
                parts.append(f"Space weather: {activity} (Kp {sw.kp_current:.0f}).")
                if sw.aurora_visibility:
                    parts.append(f"Aurora: {sw.aurora_visibility}.")
            elif sw.kp_current >= 4:
                parts.append(
                    f"Space weather is active (Kp {sw.kp_current:.0f}) - aurora possible at high latitudes."
                )
            # Don't mention quiet space weather to keep briefing concise

    # Build final briefing
    if len(parts) <= 1:
        parts.append("Sky data is currently unavailable. Please check back later.")

    return "\n".join(parts)


class DailyBriefing:
    """Client for generating daily sky briefings.

    Aggregates data from all available APIs to create a comprehensive
    summary of sky events for the entire day.

    Designed to be easily callable from external tools like Moltbot
    cron jobs for automated morning briefings.

    Example:
        ```python
        async with DailyBriefing() as briefing:
            data = await briefing.get_briefing(
                latitude=40.7128,
                longitude=-74.0060,
            )
            print(data.summary_text)  # Human-readable
            print(data.as_dict())     # Structured data
        ```
    """

    def __init__(self, timeout: float = 15.0):
        """Initialize the DailyBriefing client."""
        self.timeout = timeout

        # Lazy-loaded clients
        self._sun_client = None
        self._moon_client = None
        self._iss_client = None
        self._planet_client = None
        self._meteor_client = None
        self._eclipse_client = None
        self._aurora_client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _get_sun_client(self):
        """Lazy-load sun client."""
        if self._sun_client is None:
            from .sun import SunClient

            self._sun_client = SunClient(timeout=self.timeout)
        return self._sun_client

    async def _get_moon_client(self):
        """Lazy-load moon client."""
        if self._moon_client is None:
            from .moon import MoonClient

            self._moon_client = MoonClient(timeout=self.timeout)
        return self._moon_client

    async def _get_iss_client(self):
        """Lazy-load ISS client."""
        if self._iss_client is None:
            from .iss import ISSClient

            self._iss_client = ISSClient(timeout=self.timeout)
        return self._iss_client

    async def _get_planet_client(self):
        """Lazy-load planet client."""
        if self._planet_client is None:
            from .planets import PlanetClient

            self._planet_client = PlanetClient()
        return self._planet_client

    async def _get_meteor_client(self):
        """Lazy-load meteor client."""
        if self._meteor_client is None:
            from .meteors import MeteorClient

            self._meteor_client = MeteorClient()
        return self._meteor_client

    async def _get_eclipse_client(self):
        """Lazy-load eclipse client."""
        if self._eclipse_client is None:
            from .eclipses import EclipseClient

            self._eclipse_client = EclipseClient()
        return self._eclipse_client

    async def _get_aurora_client(self):
        """Lazy-load aurora client."""
        if self._aurora_client is None:
            from .aurora import AuroraClient

            self._aurora_client = AuroraClient(timeout=self.timeout)
        return self._aurora_client

    async def _get_sun_data(
        self,
        latitude: float,
        longitude: float,
        target_date: date,
    ) -> tuple[str | None, str | None, str | None]:
        """
        Get sun times.

        Returns:
            Tuple of (sunrise, sunset, day_length) as formatted strings
        """
        try:
            client = await self._get_sun_client()
            sun_times = await client.get_sun_times(
                latitude=latitude,
                longitude=longitude,
                target_date=target_date,
            )

            if sun_times:
                sunrise = sun_times.sunrise.strftime("%H:%M")
                sunset = sun_times.sunset.strftime("%H:%M")
                day_length = sun_times.day_length
                return (sunrise, sunset, day_length)
        except Exception as e:
            logger.warning(f"Failed to get sun data: {e}")

        return (None, None, None)

    async def _get_moon_data(
        self,
        target_date: date,
        latitude: float,
        longitude: float,
    ) -> tuple[str | None, int | None, str | None, str | None]:
        """
        Get moon phase and times.

        Returns:
            Tuple of (phase_name, illumination%, rise_time, set_time)
        """
        try:
            client = await self._get_moon_client()
            info = await client.get_moon_info(
                target_date=target_date,
                latitude=latitude,
                longitude=longitude,
            )

            phase_name = info.phase.value if info.phase else None
            illumination = info.illumination_percent

            # Note: Moon rise/set times would need USNO rstt API
            # For now, return None for times (can be added later)
            return (phase_name, illumination, None, None)
        except Exception as e:
            logger.warning(f"Failed to get moon data: {e}")
            return (None, None, None, None)

    async def _get_iss_data(
        self,
        latitude: float,
        longitude: float,
        target_date: date,
    ) -> list[str]:
        """
        Get all ISS passes for the day (including daytime).

        Returns:
            List of pass descriptions
        """
        try:
            client = await self._get_iss_client()
            passes = await client.get_passes(
                latitude=latitude,
                longitude=longitude,
                days=2,  # Include passes that might be late evening to early morning
                min_elevation=10.0,  # Lower threshold for daily briefing
            )

            # Filter to passes on target_date and format for display
            pass_strs = []
            for p in passes:
                if p.rise_time.date() == target_date:
                    time_str = p.rise_time.strftime("%H:%M")
                    visibility = "(visible)" if p.is_visible else "(daylight)"
                    pass_strs.append(f"{time_str} for {p.duration_minutes}min {visibility}")

            return pass_strs[:6]  # Limit to 6 passes
        except Exception as e:
            logger.warning(f"Failed to get ISS data: {e}")
            return []

    async def _get_planets_data(
        self,
        target_date: date,
    ) -> list[str]:
        """
        Get visible planets.

        Returns:
            List of planet names
        """
        try:
            client = await self._get_planet_client()
            planets = await client.get_visible_planets(on_date=target_date)

            return [p.planet.name for p in planets]
        except Exception as e:
            logger.warning(f"Failed to get planet data: {e}")
            return []

    async def _get_meteor_data(
        self,
        target_date: date,
    ) -> list[str]:
        """
        Get active meteor showers.

        Returns:
            List of shower names
        """
        try:
            client = await self._get_meteor_client()
            showers = await client.get_active_showers()

            return [s.shower.name for s in showers]
        except Exception as e:
            logger.warning(f"Failed to get meteor data: {e}")
            return []

    async def _get_eclipse_data(
        self,
        target_date: date,
    ) -> str | None:
        """
        Check if there's an eclipse today.

        Returns:
            Eclipse description string or None
        """
        try:
            from .eclipses import get_eclipse_info

            eclipse = get_eclipse_info(target_date)
            if eclipse:
                regions = ", ".join(eclipse.visibility_regions[:3])
                return f"{eclipse.eclipse_type.value} - visible from {regions}"
        except Exception as e:
            logger.warning(f"Failed to get eclipse data: {e}")

        return None

    async def _get_space_weather_data(self) -> SpaceWeatherSummary | None:
        """
        Get space weather summary.

        Returns:
            SpaceWeatherSummary or None
        """
        try:
            client = await self._get_aurora_client()

            # Get aurora forecast (includes Kp)
            forecast = await client.get_aurora_forecast()
            if not forecast:
                return None

            # Get solar wind
            solar_wind = await client.get_solar_wind()

            return SpaceWeatherSummary(
                kp_current=forecast.kp_current,
                kp_24h_max=forecast.kp_24h_max,
                activity_level=forecast.activity.name.replace("_", " ").title(),
                solar_wind_speed=solar_wind.speed_km_s if solar_wind else None,
                aurora_visibility=forecast.can_see_aurora if forecast.kp_current >= 4 else None,
            )
        except Exception as e:
            logger.warning(f"Failed to get space weather data: {e}")
            return None

    async def get_briefing(
        self,
        latitude: float,
        longitude: float,
        target_date: date | None = None,
    ) -> DailyBriefingData:
        """
        Get a complete daily briefing for a location.

        Fetches data from all available sources and generates
        both structured data and a human-readable summary.

        Args:
            latitude: Observer latitude
            longitude: Observer longitude
            target_date: Date to get briefing for (defaults to today)

        Returns:
            DailyBriefingData with all available information
        """
        if target_date is None:
            target_date = date.today()

        data = DailyBriefingData(date=target_date)

        # Fetch all data, handling failures gracefully
        try:
            sunrise, sunset, day_length = await self._get_sun_data(
                latitude=latitude,
                longitude=longitude,
                target_date=target_date,
            )
            data.sunrise = sunrise
            data.sunset = sunset
            data.day_length = day_length
        except Exception as e:
            logger.error(f"Sun data fetch failed: {e}")

        try:
            moon_phase, moon_illum, moon_rise, moon_set = await self._get_moon_data(
                target_date=target_date,
                latitude=latitude,
                longitude=longitude,
            )
            data.moon_phase = moon_phase
            data.moon_illumination = moon_illum
            data.moon_rise = moon_rise
            data.moon_set = moon_set
        except Exception as e:
            logger.error(f"Moon data fetch failed: {e}")

        try:
            data.iss_passes = await self._get_iss_data(
                latitude=latitude,
                longitude=longitude,
                target_date=target_date,
            )
        except Exception as e:
            logger.error(f"ISS data fetch failed: {e}")

        try:
            data.visible_planets = await self._get_planets_data(target_date=target_date)
        except Exception as e:
            logger.error(f"Planet data fetch failed: {e}")

        try:
            data.active_meteor_showers = await self._get_meteor_data(target_date=target_date)
        except Exception as e:
            logger.error(f"Meteor data fetch failed: {e}")

        try:
            data.eclipse_today = await self._get_eclipse_data(target_date=target_date)
        except Exception as e:
            logger.error(f"Eclipse data fetch failed: {e}")

        try:
            data.space_weather = await self._get_space_weather_data()
        except Exception as e:
            logger.error(f"Space weather fetch failed: {e}")

        # Generate summary text
        data.summary_text = generate_briefing_text(data)

        return data

    async def close(self) -> None:
        """Close all HTTP clients."""
        if self._sun_client:
            await self._sun_client.close()
        if self._moon_client:
            await self._moon_client.close()
        if self._iss_client:
            await self._iss_client.close()
        if self._planet_client:
            await self._planet_client.close()
        if self._meteor_client:
            await self._meteor_client.close()
        if self._eclipse_client:
            await self._eclipse_client.close()
        if self._aurora_client:
            await self._aurora_client.close()
