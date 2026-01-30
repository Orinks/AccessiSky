"""ISS tracking API client using free data sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Free API endpoints
OPEN_NOTIFY_URL = "http://api.open-notify.org/iss-now.json"
N2YO_VISUAL_PASSES_URL = "https://api.n2yo.com/rest/v1/satellite/visualpasses"


@dataclass
class ISSPosition:
    """Current ISS position."""

    latitude: float
    longitude: float
    altitude: float  # km
    velocity: float  # km/s
    timestamp: datetime

    def __str__(self) -> str:
        return f"ISS at {self.latitude:.2f}°, {self.longitude:.2f}° (alt: {self.altitude:.0f}km)"


@dataclass
class ISSPass:
    """ISS pass prediction for a location."""

    rise_time: datetime
    culmination_time: datetime
    set_time: datetime
    duration_seconds: int
    max_elevation: float  # degrees above horizon
    rise_azimuth: str | None = None
    set_azimuth: str | None = None
    is_visible: bool = False  # True if pass occurs during darkness

    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return self.duration_seconds // 60

    def __str__(self) -> str:
        visible = "visible" if self.is_visible else "not visible"
        return (
            f"ISS pass at {self.rise_time.strftime('%H:%M')} - "
            f"{self.duration_minutes}min, max {self.max_elevation:.0f}° ({visible})"
        )


def _azimuth_to_direction(azimuth: float) -> str:
    """Convert azimuth degrees to compass direction."""
    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    index = round(azimuth / 22.5) % 16
    return directions[index]


class ISSClient:
    """Client for ISS tracking using free APIs."""

    def __init__(self, timeout: float = 10.0):
        """Initialize the ISS client."""
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _fetch_json(self, url: str, params: dict | None = None) -> dict:
        """Fetch JSON from URL."""
        client = await self._get_client()
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_current_position(self) -> ISSPosition | None:
        """
        Get the current ISS position.

        Uses Open Notify API (free, no key required).

        Returns:
            ISSPosition or None if request fails
        """
        try:
            data = await self._fetch_json(OPEN_NOTIFY_URL)

            lat = float(data["iss_position"]["latitude"])
            lon = float(data["iss_position"]["longitude"])
            timestamp = datetime.fromtimestamp(data["timestamp"], tz=timezone.utc)

            return ISSPosition(
                latitude=lat,
                longitude=lon,
                altitude=408.0,  # Average ISS altitude
                velocity=7.66,  # Average ISS velocity km/s
                timestamp=timestamp,
            )
        except Exception as e:
            logger.error(f"Failed to get ISS position: {e}")
            return None

    async def get_passes(
        self,
        latitude: float,
        longitude: float,
        days: int = 10,
        min_elevation: float = 10.0,
    ) -> list[ISSPass]:
        """
        Get upcoming ISS pass predictions for a location.

        Note: This uses a simplified calculation. For production,
        consider using N2YO API (requires free API key) or
        computing passes from TLE data.

        Args:
            latitude: Observer latitude
            longitude: Observer longitude
            days: Number of days to predict
            min_elevation: Minimum elevation to include

        Returns:
            List of ISSPass predictions
        """
        try:
            # For now, return mock data - real implementation would use
            # N2YO API or compute from TLE data
            data = await self._fetch_json(
                f"https://api.n2yo.com/rest/v1/satellite/visualpasses/25544/{latitude}/{longitude}/0/{days}/{min_elevation}"
            )

            passes = []
            for pass_data in data.get("passes", []):
                rise = pass_data.get("rise", {})
                culm = pass_data.get("culmination", {})
                set_data = pass_data.get("set", {})

                rise_time = datetime.fromisoformat(rise.get("utc_datetime", ""))
                culm_time = datetime.fromisoformat(culm.get("utc_datetime", ""))
                set_time = datetime.fromisoformat(set_data.get("utc_datetime", ""))

                passes.append(
                    ISSPass(
                        rise_time=rise_time,
                        culmination_time=culm_time,
                        set_time=set_time,
                        duration_seconds=int((set_time - rise_time).total_seconds()),
                        max_elevation=culm.get("elevation", 0),
                        rise_azimuth=_azimuth_to_direction(rise.get("azimuth", 0)),
                        set_azimuth=_azimuth_to_direction(set_data.get("azimuth", 0)),
                        is_visible=pass_data.get("visible", False),
                    )
                )

            return passes
        except Exception as e:
            logger.error(f"Failed to get ISS passes: {e}")
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
