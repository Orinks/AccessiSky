"""Sun times API client using sunrise-sunset.org (free, no API key)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

SUNRISE_SUNSET_API = "https://api.sunrise-sunset.org/json"


@dataclass
class SunTimes:
    """Sun times for a specific date and location."""

    date: date
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime
    day_length_seconds: int
    civil_twilight_begin: datetime
    civil_twilight_end: datetime
    nautical_twilight_begin: datetime
    nautical_twilight_end: datetime
    astronomical_twilight_begin: datetime
    astronomical_twilight_end: datetime

    @property
    def day_length(self) -> str:
        """Get day length as formatted string."""
        hours = self.day_length_seconds // 3600
        minutes = (self.day_length_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    @property
    def golden_hour_morning_end(self) -> datetime:
        """Approximate end of morning golden hour (1 hour after sunrise)."""
        return self.sunrise + timedelta(hours=1)

    @property
    def golden_hour_evening_start(self) -> datetime:
        """Approximate start of evening golden hour (1 hour before sunset)."""
        return self.sunset - timedelta(hours=1)

    def __str__(self) -> str:
        return (
            f"Sunrise: {self.sunrise.strftime('%H:%M')}, "
            f"Sunset: {self.sunset.strftime('%H:%M')}, "
            f"Day length: {self.day_length}"
        )


def _parse_time(time_str: str, target_date: date) -> datetime:
    """Parse time string from API response.

    API returns times in 12-hour format like "7:27:02 AM"
    Times are in UTC.
    """
    from datetime import timezone

    # Parse time (API returns UTC times)
    time_obj = datetime.strptime(time_str, "%I:%M:%S %p").time()
    return datetime.combine(target_date, time_obj, tzinfo=timezone.utc)


def _parse_day_length(length_str: str) -> int:
    """Parse day length string to seconds.

    API returns format like "10:59:14" (HH:MM:SS)
    """
    parts = length_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    return hours * 3600 + minutes * 60 + seconds


class SunClient:
    """Client for sun times using sunrise-sunset.org API."""

    def __init__(self, timeout: float = 10.0):
        """Initialize the sun client."""
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get_sun_times(
        self,
        latitude: float,
        longitude: float,
        target_date: date | None = None,
    ) -> SunTimes | None:
        """
        Get sun times for a location and date.

        Args:
            latitude: Observer latitude (-90 to 90)
            longitude: Observer longitude (-180 to 180)
            target_date: Date to get times for (defaults to today)

        Returns:
            SunTimes object or None if request fails
        """
        if target_date is None:
            target_date = date.today()

        try:
            client = await self._get_client()
            response = await client.get(
                SUNRISE_SUNSET_API,
                params={
                    "lat": latitude,
                    "lng": longitude,
                    "date": target_date.isoformat(),
                    "formatted": 0,  # Get ISO 8601 formatted times
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                logger.error(f"API error: {data.get('status')}")
                return None

            results = data["results"]

            # API with formatted=0 returns ISO 8601 timestamps

            def parse_iso(s: str) -> datetime:
                # Handle both Z suffix and +00:00 suffix
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                return datetime.fromisoformat(s)

            return SunTimes(
                date=target_date,
                sunrise=parse_iso(results["sunrise"]),
                sunset=parse_iso(results["sunset"]),
                solar_noon=parse_iso(results["solar_noon"]),
                day_length_seconds=results["day_length"],
                civil_twilight_begin=parse_iso(results["civil_twilight_begin"]),
                civil_twilight_end=parse_iso(results["civil_twilight_end"]),
                nautical_twilight_begin=parse_iso(results["nautical_twilight_begin"]),
                nautical_twilight_end=parse_iso(results["nautical_twilight_end"]),
                astronomical_twilight_begin=parse_iso(results["astronomical_twilight_begin"]),
                astronomical_twilight_end=parse_iso(results["astronomical_twilight_end"]),
            )

        except Exception as e:
            logger.error(f"Failed to get sun times: {e}")
            return None

    async def get_sun_times_range(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        days: int = 7,
    ) -> list[SunTimes]:
        """
        Get sun times for multiple days.

        Args:
            latitude: Observer latitude
            longitude: Observer longitude
            start_date: First date
            days: Number of days to fetch

        Returns:
            List of SunTimes objects
        """
        results = []
        for i in range(days):
            target_date = start_date + timedelta(days=i)
            sun_times = await self.get_sun_times(latitude, longitude, target_date)
            if sun_times:
                results.append(sun_times)
        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
