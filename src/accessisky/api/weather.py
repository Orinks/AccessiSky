"""Weather API client using Open-Meteo (free, no API key required).

Open-Meteo provides high-quality weather data including:
- Cloud cover (total, low, mid, high)
- Visibility
- Precipitation
- Temperature
- Wind

This is particularly useful for determining stargazing conditions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"


@dataclass
class HourlyWeather:
    """Weather data for a specific hour."""

    time: datetime
    cloud_cover_percent: float  # Total cloud cover 0-100%
    cloud_cover_low_percent: float | None = None
    cloud_cover_mid_percent: float | None = None
    cloud_cover_high_percent: float | None = None
    visibility_meters: float | None = None
    temperature_celsius: float | None = None
    humidity_percent: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    is_day: bool | None = None

    @property
    def visibility_km(self) -> float | None:
        """Get visibility in kilometers."""
        if self.visibility_meters is None:
            return None
        return self.visibility_meters / 1000

    @property
    def is_clear(self) -> bool:
        """Check if sky is clear (< 20% cloud cover)."""
        return self.cloud_cover_percent < 20

    @property
    def is_good_for_stargazing(self) -> bool:
        """Quick check if conditions are good for stargazing."""
        return (
            self.cloud_cover_percent < 30
            and (self.visibility_meters is None or self.visibility_meters > 10000)
            and self.is_day is False
        )


@dataclass
class DailyWeather:
    """Weather summary for a day."""

    date: date
    cloud_cover_mean_percent: float
    cloud_cover_min_percent: float
    cloud_cover_max_percent: float
    visibility_mean_meters: float | None = None
    temperature_max_celsius: float | None = None
    temperature_min_celsius: float | None = None
    precipitation_sum_mm: float | None = None

    @property
    def best_for_stargazing(self) -> bool:
        """Check if day has potential for good stargazing (low clouds at night)."""
        return self.cloud_cover_min_percent < 30


@dataclass
class WeatherForecast:
    """Complete weather forecast."""

    latitude: float
    longitude: float
    timezone: str
    hourly: list[HourlyWeather]
    daily_summary: DailyWeather | None = None

    def get_nighttime_conditions(
        self,
        target_date: date | None = None,
    ) -> list[HourlyWeather]:
        """
        Get weather conditions for nighttime hours.

        Args:
            target_date: Date to get nighttime conditions for

        Returns:
            List of HourlyWeather for night hours (is_day=False)
        """
        if target_date is None:
            target_date = date.today()

        return [h for h in self.hourly if h.is_day is False and h.time.date() == target_date]

    def get_best_hour_for_stargazing(
        self,
        target_date: date | None = None,
    ) -> HourlyWeather | None:
        """
        Find the best hour for stargazing on a given date.

        Args:
            target_date: Date to check

        Returns:
            HourlyWeather with lowest cloud cover at night, or None
        """
        nighttime = self.get_nighttime_conditions(target_date)
        if not nighttime:
            return None

        return min(nighttime, key=lambda h: h.cloud_cover_percent)


class WeatherClient:
    """Client for weather data using Open-Meteo API."""

    def __init__(self, timeout: float = 10.0):
        """Initialize the weather client."""
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get_hourly_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 3,
        include_visibility: bool = True,
        include_temperature: bool = False,
        include_precipitation: bool = False,
        include_wind: bool = False,
    ) -> WeatherForecast | None:
        """
        Get hourly weather forecast for a location.

        Args:
            latitude: Observer latitude
            longitude: Observer longitude
            forecast_days: Number of days to forecast (1-16)
            include_visibility: Include visibility data
            include_temperature: Include temperature data
            include_precipitation: Include precipitation data
            include_wind: Include wind data

        Returns:
            WeatherForecast or None if request fails
        """
        try:
            client = await self._get_client()

            # Build hourly variables list
            hourly_vars = [
                "cloud_cover",
                "cloud_cover_low",
                "cloud_cover_mid",
                "cloud_cover_high",
                "is_day",
            ]
            if include_visibility:
                hourly_vars.append("visibility")
            if include_temperature:
                hourly_vars.extend(["temperature_2m", "relative_humidity_2m"])
            if include_precipitation:
                hourly_vars.append("precipitation")
            if include_wind:
                hourly_vars.append("wind_speed_10m")

            response = await client.get(
                OPEN_METEO_API,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": ",".join(hourly_vars),
                    "forecast_days": min(forecast_days, 16),
                    "timezone": "UTC",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Parse hourly data
            hourly_data = data.get("hourly", {})
            times = hourly_data.get("time", [])
            cloud_cover = hourly_data.get("cloud_cover", [])
            cloud_cover_low = hourly_data.get("cloud_cover_low", [])
            cloud_cover_mid = hourly_data.get("cloud_cover_mid", [])
            cloud_cover_high = hourly_data.get("cloud_cover_high", [])
            visibility = hourly_data.get("visibility", [])
            temperature = hourly_data.get("temperature_2m", [])
            humidity = hourly_data.get("relative_humidity_2m", [])
            precipitation = hourly_data.get("precipitation", [])
            wind_speed = hourly_data.get("wind_speed_10m", [])
            is_day = hourly_data.get("is_day", [])

            hourly: list[HourlyWeather] = []
            for i, time_str in enumerate(times):
                # Parse ISO time
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

                hourly.append(
                    HourlyWeather(
                        time=dt,
                        cloud_cover_percent=cloud_cover[i] if i < len(cloud_cover) else 0,
                        cloud_cover_low_percent=cloud_cover_low[i]
                        if i < len(cloud_cover_low)
                        else None,
                        cloud_cover_mid_percent=cloud_cover_mid[i]
                        if i < len(cloud_cover_mid)
                        else None,
                        cloud_cover_high_percent=cloud_cover_high[i]
                        if i < len(cloud_cover_high)
                        else None,
                        visibility_meters=visibility[i] if i < len(visibility) else None,
                        temperature_celsius=temperature[i] if i < len(temperature) else None,
                        humidity_percent=humidity[i] if i < len(humidity) else None,
                        precipitation_mm=precipitation[i] if i < len(precipitation) else None,
                        wind_speed_kmh=wind_speed[i] if i < len(wind_speed) else None,
                        is_day=bool(is_day[i]) if i < len(is_day) else None,
                    )
                )

            return WeatherForecast(
                latitude=data.get("latitude", latitude),
                longitude=data.get("longitude", longitude),
                timezone=data.get("timezone", "UTC"),
                hourly=hourly,
            )

        except Exception as e:
            logger.error(f"Failed to get weather forecast: {e}")
            return None

    async def get_current_cloud_cover(
        self,
        latitude: float,
        longitude: float,
    ) -> float | None:
        """
        Get current cloud cover percentage.

        Args:
            latitude: Observer latitude
            longitude: Observer longitude

        Returns:
            Cloud cover percentage (0-100) or None if request fails
        """
        forecast = await self.get_hourly_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=1,
            include_visibility=False,
        )

        if forecast and forecast.hourly:
            # Find current hour
            now = datetime.now(timezone.utc)
            for hour in forecast.hourly:
                if hour.time.hour == now.hour and hour.time.date() == now.date():
                    return hour.cloud_cover_percent

            # If exact hour not found, return first hour
            return forecast.hourly[0].cloud_cover_percent

        return None

    async def get_stargazing_conditions(
        self,
        latitude: float,
        longitude: float,
        target_date: date | None = None,
    ) -> dict:
        """
        Get stargazing-relevant weather conditions.

        Args:
            latitude: Observer latitude
            longitude: Observer longitude
            target_date: Date to check (defaults to today)

        Returns:
            Dictionary with stargazing conditions
        """
        if target_date is None:
            target_date = date.today()

        forecast = await self.get_hourly_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=2,  # Get today and tomorrow for nighttime coverage
            include_visibility=True,
        )

        if not forecast:
            return {
                "available": False,
                "error": "Failed to fetch weather data",
            }

        nighttime = forecast.get_nighttime_conditions(target_date)
        best_hour = forecast.get_best_hour_for_stargazing(target_date)

        if not nighttime:
            return {
                "available": True,
                "has_nighttime_data": False,
                "forecast": forecast,
            }

        avg_cloud_cover = sum(h.cloud_cover_percent for h in nighttime) / len(nighttime)
        min_cloud_cover = min(h.cloud_cover_percent for h in nighttime)

        return {
            "available": True,
            "has_nighttime_data": True,
            "nighttime_hours": len(nighttime),
            "avg_cloud_cover_percent": round(avg_cloud_cover, 1),
            "min_cloud_cover_percent": round(min_cloud_cover, 1),
            "best_hour": best_hour,
            "forecast": forecast,
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
