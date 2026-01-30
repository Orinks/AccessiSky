"""Tonight's Summary API - aggregates all sky data for tonight.

Provides a plain-language summary of what's happening in the sky tonight,
designed for blind/VI users who want a quick overview.
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
class TonightData:
    """Aggregated data about tonight's sky."""

    # Moon data
    moon_phase: str | None = None
    moon_illumination: int | None = None  # 0-100
    moon_rise_time: str | None = None
    moon_set_time: str | None = None

    # ISS passes
    iss_passes: list[str] = field(default_factory=list)

    # Visible planets
    visible_planets: list[str] = field(default_factory=list)

    # Meteor showers
    active_meteor_showers: list[str] = field(default_factory=list)

    # Aurora
    aurora_kp: float | None = None
    aurora_activity: str | None = None

    # Viewing conditions
    viewing_score: int | None = None  # 0-100
    cloud_cover_percent: int | None = None
    viewing_description: str | None = None

    # Generated summary
    summary_text: str | None = None


def generate_summary_text(data: TonightData) -> str:
    """
    Generate a human-readable summary from TonightData.

    Creates a natural language description suitable for screen readers.

    Args:
        data: TonightData with aggregated sky information

    Returns:
        Plain-language summary string
    """
    parts = ["Tonight:"]

    # Moon info
    if data.moon_phase:
        moon_str = f"{data.moon_phase}"
        if data.moon_illumination is not None:
            moon_str += f" ({data.moon_illumination}% illuminated)"
        if data.moon_rise_time:
            moon_str += f" rises at {data.moon_rise_time}"
        elif data.moon_set_time:
            moon_str += f" sets at {data.moon_set_time}"
        parts.append(moon_str + ".")

    # ISS passes
    if data.iss_passes:
        if len(data.iss_passes) == 1:
            parts.append(f"The ISS passes over at {data.iss_passes[0]}.")
        else:
            parts.append(f"The ISS has {len(data.iss_passes)} visible passes tonight.")
    # Don't mention if no passes - keeps summary cleaner

    # Visible planets
    if data.visible_planets:
        if len(data.visible_planets) == 1:
            parts.append(f"{data.visible_planets[0]} is visible in the sky.")
        elif len(data.visible_planets) == 2:
            parts.append(
                f"{data.visible_planets[0]} and {data.visible_planets[1]} are visible in the evening sky."
            )
        else:
            planet_list = ", ".join(data.visible_planets[:-1])
            planet_list += f", and {data.visible_planets[-1]}"
            parts.append(f"{planet_list} are visible tonight.")

    # Meteor showers
    if data.active_meteor_showers:
        if len(data.active_meteor_showers) == 1:
            parts.append(f"The {data.active_meteor_showers[0]} meteor shower is active.")
        else:
            showers = " and ".join(data.active_meteor_showers[:2])
            parts.append(f"The {showers} meteor showers are active.")

    # Aurora activity
    if data.aurora_kp is not None and data.aurora_kp >= 4:
        activity = data.aurora_activity or "elevated"
        parts.append(f"Aurora activity is {activity.lower()} (Kp {data.aurora_kp:.0f}).")
    elif data.aurora_kp is not None and data.aurora_kp >= 3:
        parts.append("Aurora may be visible at high latitudes.")

    # Viewing conditions
    if data.viewing_score is not None:
        if data.viewing_score >= 80:
            condition = "excellent"
        elif data.viewing_score >= 60:
            condition = "good"
        elif data.viewing_score >= 40:
            condition = "fair"
        else:
            condition = "poor"

        condition_str = f"Viewing conditions are {condition} ({data.viewing_score}/100)"

        if data.cloud_cover_percent is not None and data.cloud_cover_percent >= 50:
            if data.cloud_cover_percent >= 75:
                condition_str += " with overcast skies"
            else:
                condition_str += " with partly cloudy skies"
        elif data.viewing_description:
            condition_str += f" - {data.viewing_description.lower()}"

        parts.append(condition_str + ".")

    # Build final summary
    if len(parts) == 1:
        # No data available
        parts.append("Sky data is currently unavailable. Please check back later.")

    return " ".join(parts)


class TonightSummary:
    """Client for generating tonight's sky summary.

    Aggregates data from all available APIs to create a comprehensive
    but concise summary of tonight's sky conditions.
    """

    def __init__(self, timeout: float = 15.0):
        """Initialize the TonightSummary client."""
        self.timeout = timeout

        # Lazy-loaded clients
        self._moon_client = None
        self._iss_client = None
        self._planet_client = None
        self._meteor_client = None
        self._aurora_client = None
        self._viewing_client = None

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

    async def _get_aurora_client(self):
        """Lazy-load aurora client."""
        if self._aurora_client is None:
            from .aurora import AuroraClient

            self._aurora_client = AuroraClient(timeout=self.timeout)
        return self._aurora_client

    async def _get_viewing_client(self):
        """Lazy-load viewing conditions client."""
        if self._viewing_client is None:
            from .viewing import ViewingClient

            self._viewing_client = ViewingClient(timeout=self.timeout)
        return self._viewing_client

    async def _get_moon_data(
        self,
        target_date: date | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
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

            # Note: Moon rise/set times would need a separate API call
            # For now, return None for times
            return (phase_name, illumination, None, None)
        except Exception as e:
            logger.warning(f"Failed to get moon data: {e}")
            return (None, None, None, None)

    async def _get_iss_data(
        self,
        latitude: float,
        longitude: float,
    ) -> list[str]:
        """
        Get tonight's ISS passes.

        Returns:
            List of pass descriptions
        """
        try:
            client = await self._get_iss_client()
            passes = await client.get_passes(
                latitude=latitude,
                longitude=longitude,
                days=1,
                min_elevation=20.0,
            )

            # Format passes for display
            pass_strs = []
            for p in passes[:3]:  # Limit to 3 passes
                time_str = p.rise_time.strftime("%H:%M")
                pass_strs.append(f"{time_str} for {p.duration_minutes} minutes")

            return pass_strs
        except Exception as e:
            logger.warning(f"Failed to get ISS data: {e}")
            return []

    async def _get_planets_data(
        self,
        target_date: date | None = None,
    ) -> list[str]:
        """
        Get visible planets tonight.

        Returns:
            List of planet names
        """
        try:
            client = await self._get_planet_client()
            planets = await client.get_visible_planets(on_date=target_date)

            # Return just the names, sorted by brightness
            return [p.planet.name for p in planets]
        except Exception as e:
            logger.warning(f"Failed to get planet data: {e}")
            return []

    async def _get_meteor_data(
        self,
        target_date: date | None = None,
    ) -> list[str]:
        """
        Get active meteor showers.

        Returns:
            List of shower names
        """
        try:
            client = await self._get_meteor_client()
            showers = await client.get_active_showers()

            # Return just the names
            return [s.shower.name for s in showers]
        except Exception as e:
            logger.warning(f"Failed to get meteor data: {e}")
            return []

    async def _get_aurora_data(self) -> tuple[float | None, str | None]:
        """
        Get aurora activity level.

        Returns:
            Tuple of (kp_index, activity_description)
        """
        try:
            client = await self._get_aurora_client()
            forecast = await client.get_aurora_forecast()

            if forecast:
                return (forecast.kp_current, forecast.activity.name)
            return (None, None)
        except Exception as e:
            logger.warning(f"Failed to get aurora data: {e}")
            return (None, None)

    async def _get_viewing_data(
        self,
        latitude: float,
        longitude: float,
        target_date: date | None = None,
    ) -> tuple[int | None, int | None, str | None]:
        """
        Get viewing conditions.

        Returns:
            Tuple of (score, cloud_cover%, description)
        """
        try:
            client = await self._get_viewing_client()
            conditions = await client.get_viewing_conditions_for_location(
                latitude=latitude,
                longitude=longitude,
                target_date=target_date,
            )

            return (
                conditions.numeric_score,
                int(conditions.cloud_cover.value.split()[0]) if conditions.cloud_cover else None,
                conditions.summary,
            )
        except Exception as e:
            logger.warning(f"Failed to get viewing data: {e}")
            return (None, None, None)

    async def get_summary(
        self,
        latitude: float,
        longitude: float,
        target_date: date | None = None,
    ) -> TonightData:
        """
        Get a complete summary of tonight's sky.

        Fetches data from all available sources and generates
        a human-readable summary.

        Args:
            latitude: Observer latitude
            longitude: Observer longitude
            target_date: Date to get summary for (defaults to today)

        Returns:
            TonightData with all available information
        """
        if target_date is None:
            target_date = date.today()

        data = TonightData()

        # Fetch all data, handling failures gracefully
        try:
            moon_phase, moon_illum, moon_rise, moon_set = await self._get_moon_data(
                target_date=target_date,
                latitude=latitude,
                longitude=longitude,
            )
            data.moon_phase = moon_phase
            data.moon_illumination = moon_illum
            data.moon_rise_time = moon_rise
            data.moon_set_time = moon_set
        except Exception as e:
            logger.error(f"Moon data fetch failed: {e}")

        try:
            data.iss_passes = await self._get_iss_data(
                latitude=latitude,
                longitude=longitude,
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
            aurora_kp, aurora_activity = await self._get_aurora_data()
            data.aurora_kp = aurora_kp
            data.aurora_activity = aurora_activity
        except Exception as e:
            logger.error(f"Aurora data fetch failed: {e}")

        try:
            score, cloud_cover, description = await self._get_viewing_data(
                latitude=latitude,
                longitude=longitude,
                target_date=target_date,
            )
            data.viewing_score = score
            data.cloud_cover_percent = cloud_cover
            data.viewing_description = description
        except Exception as e:
            logger.error(f"Viewing data fetch failed: {e}")

        # Generate summary text
        data.summary_text = generate_summary_text(data)

        return data

    async def close(self) -> None:
        """Close all HTTP clients."""
        if self._moon_client:
            await self._moon_client.close()
        if self._iss_client:
            await self._iss_client.close()
        if self._planet_client:
            await self._planet_client.close()
        if self._meteor_client:
            await self._meteor_client.close()
        if self._aurora_client:
            await self._aurora_client.close()
        if self._viewing_client:
            await self._viewing_client.close()
