"""Aurora and space weather API client using NOAA SWPC."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# NOAA Space Weather Prediction Center endpoints (free, no API key)
SWPC_BASE = "https://services.swpc.noaa.gov"
KP_INDEX_URL = f"{SWPC_BASE}/products/noaa-planetary-k-index.json"
AURORA_FORECAST_URL = f"{SWPC_BASE}/text/aurora-nowcast-hemi-power.txt"
SOLAR_WIND_URL = f"{SWPC_BASE}/products/solar-wind/plasma-7-day.json"
GEOMAG_FORECAST_URL = f"{SWPC_BASE}/products/noaa-planetary-k-index-forecast.json"


class GeomagActivity(IntEnum):
    """Geomagnetic activity levels based on Kp index."""

    QUIET = 0  # Kp 0-1
    UNSETTLED = 1  # Kp 2-3
    ACTIVE = 2  # Kp 4
    MINOR_STORM = 3  # Kp 5 (G1)
    MODERATE_STORM = 4  # Kp 6 (G2)
    STRONG_STORM = 5  # Kp 7 (G3)
    SEVERE_STORM = 6  # Kp 8 (G4)
    EXTREME_STORM = 7  # Kp 9 (G5)


def _kp_to_activity(kp: float) -> GeomagActivity:
    """Convert Kp index to activity level."""
    if kp < 2:
        return GeomagActivity.QUIET
    elif kp < 4:
        return GeomagActivity.UNSETTLED
    elif kp < 5:
        return GeomagActivity.ACTIVE
    elif kp < 6:
        return GeomagActivity.MINOR_STORM
    elif kp < 7:
        return GeomagActivity.MODERATE_STORM
    elif kp < 8:
        return GeomagActivity.STRONG_STORM
    elif kp < 9:
        return GeomagActivity.SEVERE_STORM
    else:
        return GeomagActivity.EXTREME_STORM


def _activity_description(activity: GeomagActivity) -> str:
    """Get human-readable description of activity level."""
    descriptions = {
        GeomagActivity.QUIET: "Quiet conditions, aurora unlikely except at high latitudes",
        GeomagActivity.UNSETTLED: "Unsettled conditions, aurora possible at high latitudes",
        GeomagActivity.ACTIVE: "Active conditions, aurora likely at high latitudes",
        GeomagActivity.MINOR_STORM: "G1 Minor Storm - Aurora visible at 60°+ latitude",
        GeomagActivity.MODERATE_STORM: "G2 Moderate Storm - Aurora visible at 55°+ latitude",
        GeomagActivity.STRONG_STORM: "G3 Strong Storm - Aurora visible at 50°+ latitude",
        GeomagActivity.SEVERE_STORM: "G4 Severe Storm - Aurora visible at 45°+ latitude",
        GeomagActivity.EXTREME_STORM: "G5 Extreme Storm - Aurora visible at 40°+ latitude!",
    }
    return descriptions.get(activity, "Unknown conditions")


@dataclass
class KpIndex:
    """Planetary K-index measurement."""

    timestamp: datetime
    kp: float
    activity: GeomagActivity

    @property
    def description(self) -> str:
        """Get activity description."""
        return _activity_description(self.activity)

    def __str__(self) -> str:
        return f"Kp {self.kp:.1f} - {self.activity.name}"


@dataclass
class AuroraForecast:
    """Aurora visibility forecast."""

    timestamp: datetime
    kp_current: float
    kp_24h_max: float
    activity: GeomagActivity
    hemisphere_power_gw: float | None  # Gigawatts of auroral power
    visibility_latitude: float  # Approximate southernmost latitude for visibility

    @property
    def description(self) -> str:
        """Get forecast description."""
        return _activity_description(self.activity)

    @property
    def can_see_aurora(self) -> str:
        """Get visibility description."""
        if self.visibility_latitude >= 60:
            return "Aurora may be visible from far northern regions (Alaska, Canada, Scandinavia)"
        elif self.visibility_latitude >= 55:
            return "Aurora may be visible from northern US states and southern Canada"
        elif self.visibility_latitude >= 50:
            return "Aurora may be visible from northern US, UK, and central Europe"
        elif self.visibility_latitude >= 45:
            return "Aurora may be visible across much of the US and Europe"
        else:
            return "Strong aurora event - may be visible at unusually low latitudes!"

    def __str__(self) -> str:
        return (
            f"Aurora Forecast: Kp {self.kp_current:.1f} "
            f"(24h max: {self.kp_24h_max:.1f}) - {self.activity.name}"
        )


@dataclass
class SolarWind:
    """Solar wind conditions."""

    timestamp: datetime
    speed_km_s: float  # km/s
    density_p_cm3: float  # protons/cm³
    temperature_k: float | None  # Kelvin

    @property
    def is_elevated(self) -> bool:
        """Check if solar wind is elevated."""
        return self.speed_km_s > 500 or self.density_p_cm3 > 10

    def __str__(self) -> str:
        return f"Solar wind: {self.speed_km_s:.0f} km/s, density {self.density_p_cm3:.1f}/cm³"


class AuroraClient:
    """Client for aurora and space weather data from NOAA SWPC."""

    def __init__(self, timeout: float = 15.0):
        """Initialize the aurora client."""
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get_current_kp(self) -> KpIndex | None:
        """
        Get the current planetary K-index.

        The Kp index measures geomagnetic activity (0-9 scale).
        Higher values = more aurora activity.

        Returns:
            KpIndex or None if request fails
        """
        try:
            client = await self._get_client()
            response = await client.get(KP_INDEX_URL)
            response.raise_for_status()
            data = response.json()

            # Data is array of arrays: [time_tag, Kp, Kp_fraction, a_running, station_count]
            # Skip header row, get most recent
            if len(data) < 2:
                return None

            latest = data[-1]
            time_str = latest[0]  # Format: "2026-01-30 03:00:00.000"
            kp = float(latest[1])

            timestamp = datetime.strptime(time_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
            timestamp = timestamp.replace(tzinfo=timezone.utc)

            return KpIndex(
                timestamp=timestamp,
                kp=kp,
                activity=_kp_to_activity(kp),
            )

        except Exception as e:
            logger.error(f"Failed to get Kp index: {e}")
            return None

    async def get_kp_forecast(self) -> list[KpIndex]:
        """
        Get Kp index forecast for the next 3 days.

        Returns:
            List of KpIndex predictions
        """
        try:
            client = await self._get_client()
            response = await client.get(GEOMAG_FORECAST_URL)
            response.raise_for_status()
            data = response.json()

            forecasts = []
            # Skip header row
            for row in data[1:]:
                try:
                    time_str = row[0]
                    kp = float(row[1])
                    timestamp = datetime.strptime(time_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                    forecasts.append(
                        KpIndex(
                            timestamp=timestamp,
                            kp=kp,
                            activity=_kp_to_activity(kp),
                        )
                    )
                except (IndexError, ValueError):
                    continue

            return forecasts

        except Exception as e:
            logger.error(f"Failed to get Kp forecast: {e}")
            return []

    async def get_aurora_forecast(self) -> AuroraForecast | None:
        """
        Get aurora visibility forecast.

        Combines current Kp data with forecast to give visibility info.

        Returns:
            AuroraForecast or None if request fails
        """
        try:
            # Get current Kp
            current_kp = await self.get_current_kp()
            if not current_kp:
                return None

            # Get forecast for 24h max
            forecasts = await self.get_kp_forecast()
            kp_24h_max = current_kp.kp
            for f in forecasts[:8]:  # ~24 hours of 3-hour forecasts
                kp_24h_max = max(kp_24h_max, f.kp)

            # Estimate visibility latitude based on Kp
            # Rough approximation: 67° - (Kp * 3°)
            visibility_lat = max(40, 67 - (kp_24h_max * 3))

            return AuroraForecast(
                timestamp=current_kp.timestamp,
                kp_current=current_kp.kp,
                kp_24h_max=kp_24h_max,
                activity=_kp_to_activity(kp_24h_max),
                hemisphere_power_gw=None,  # Would need to parse aurora-nowcast
                visibility_latitude=visibility_lat,
            )

        except Exception as e:
            logger.error(f"Failed to get aurora forecast: {e}")
            return None

    async def get_solar_wind(self) -> SolarWind | None:
        """
        Get current solar wind conditions.

        Returns:
            SolarWind or None if request fails
        """
        try:
            client = await self._get_client()
            response = await client.get(SOLAR_WIND_URL)
            response.raise_for_status()
            data = response.json()

            # Find most recent valid data point
            # Data format: [time_tag, density, speed, temperature]
            for row in reversed(data[1:]):
                try:
                    time_str = row[0]
                    density = float(row[1]) if row[1] else None
                    speed = float(row[2]) if row[2] else None
                    temp = float(row[3]) if row[3] else None

                    if speed is None:
                        continue

                    timestamp = datetime.strptime(time_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                    return SolarWind(
                        timestamp=timestamp,
                        speed_km_s=speed,
                        density_p_cm3=density or 0,
                        temperature_k=temp,
                    )
                except (IndexError, ValueError, TypeError):
                    continue

            return None

        except Exception as e:
            logger.error(f"Failed to get solar wind data: {e}")
            return None

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
