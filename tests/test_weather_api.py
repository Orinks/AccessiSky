"""Tests for Weather API client (Open-Meteo)."""

from datetime import date, datetime, timezone

import pytest

from accessisky.api.weather import (
    DailyWeather,
    HourlyWeather,
    WeatherClient,
    WeatherForecast,
)


class TestHourlyWeather:
    """Tests for HourlyWeather dataclass."""

    def test_hourly_weather_creation(self):
        """Test creating hourly weather data."""
        hw = HourlyWeather(
            time=datetime(2026, 1, 30, 12, 0, tzinfo=timezone.utc),
            cloud_cover_percent=25.0,
            visibility_meters=40000.0,
            is_day=True,
        )
        assert hw.cloud_cover_percent == 25.0
        assert hw.visibility_meters == 40000.0
        assert hw.is_day is True

    def test_visibility_km_property(self):
        """Test visibility in kilometers conversion."""
        hw = HourlyWeather(
            time=datetime.now(timezone.utc),
            cloud_cover_percent=0,
            visibility_meters=25000.0,
        )
        assert hw.visibility_km == 25.0

    def test_visibility_km_none(self):
        """Test visibility_km when visibility is None."""
        hw = HourlyWeather(
            time=datetime.now(timezone.utc),
            cloud_cover_percent=0,
        )
        assert hw.visibility_km is None

    def test_is_clear_property(self):
        """Test is_clear property."""
        clear = HourlyWeather(
            time=datetime.now(timezone.utc),
            cloud_cover_percent=15,
        )
        cloudy = HourlyWeather(
            time=datetime.now(timezone.utc),
            cloud_cover_percent=50,
        )
        assert clear.is_clear is True
        assert cloudy.is_clear is False

    def test_is_good_for_stargazing(self):
        """Test stargazing conditions check."""
        good = HourlyWeather(
            time=datetime.now(timezone.utc),
            cloud_cover_percent=10,
            visibility_meters=30000,
            is_day=False,
        )
        # Daytime - not good
        bad_day = HourlyWeather(
            time=datetime.now(timezone.utc),
            cloud_cover_percent=10,
            visibility_meters=30000,
            is_day=True,
        )
        # Cloudy - not good
        bad_clouds = HourlyWeather(
            time=datetime.now(timezone.utc),
            cloud_cover_percent=80,
            visibility_meters=30000,
            is_day=False,
        )
        assert good.is_good_for_stargazing is True
        assert bad_day.is_good_for_stargazing is False
        assert bad_clouds.is_good_for_stargazing is False


class TestDailyWeather:
    """Tests for DailyWeather dataclass."""

    def test_daily_weather_creation(self):
        """Test creating daily weather data."""
        dw = DailyWeather(
            date=date(2026, 1, 30),
            cloud_cover_mean_percent=40.0,
            cloud_cover_min_percent=10.0,
            cloud_cover_max_percent=80.0,
        )
        assert dw.date == date(2026, 1, 30)
        assert dw.cloud_cover_mean_percent == 40.0

    def test_best_for_stargazing(self):
        """Test best_for_stargazing property."""
        good = DailyWeather(
            date=date.today(),
            cloud_cover_mean_percent=50.0,
            cloud_cover_min_percent=10.0,  # Low minimum
            cloud_cover_max_percent=80.0,
        )
        bad = DailyWeather(
            date=date.today(),
            cloud_cover_mean_percent=70.0,
            cloud_cover_min_percent=50.0,  # High minimum
            cloud_cover_max_percent=90.0,
        )
        assert good.best_for_stargazing is True
        assert bad.best_for_stargazing is False


class TestWeatherForecast:
    """Tests for WeatherForecast dataclass."""

    @pytest.fixture
    def sample_forecast(self):
        """Create a sample forecast for testing."""
        hourly = [
            HourlyWeather(
                time=datetime(2026, 1, 30, h, 0, tzinfo=timezone.utc),
                cloud_cover_percent=20 + h * 2,
                visibility_meters=30000,
                is_day=6 <= h <= 18,
            )
            for h in range(24)
        ]
        return WeatherForecast(
            latitude=40.71,
            longitude=-74.01,
            timezone="UTC",
            hourly=hourly,
        )

    def test_get_nighttime_conditions(self, sample_forecast):
        """Test getting nighttime conditions."""
        night = sample_forecast.get_nighttime_conditions(date(2026, 1, 30))
        assert len(night) > 0
        for h in night:
            assert h.is_day is False

    def test_get_best_hour_for_stargazing(self, sample_forecast):
        """Test finding best stargazing hour."""
        best = sample_forecast.get_best_hour_for_stargazing(date(2026, 1, 30))
        # Best should be the hour with lowest cloud cover at night
        assert best is not None
        assert best.is_day is False


class TestWeatherClient:
    """Tests for WeatherClient API calls."""

    @pytest.fixture
    def client(self):
        """Create a weather client for testing."""
        return WeatherClient(timeout=10.0)

    @pytest.mark.asyncio
    async def test_get_hourly_forecast(self, client):
        """Test getting hourly forecast (live API call)."""
        forecast = await client.get_hourly_forecast(
            latitude=40.71,
            longitude=-74.01,
            forecast_days=1,
        )
        await client.close()

        assert forecast is not None
        assert len(forecast.hourly) > 0
        assert forecast.latitude == pytest.approx(40.71, abs=0.1)

    @pytest.mark.asyncio
    async def test_get_current_cloud_cover(self, client):
        """Test getting current cloud cover."""
        cloud_cover = await client.get_current_cloud_cover(
            latitude=40.71,
            longitude=-74.01,
        )
        await client.close()

        assert cloud_cover is not None
        assert 0 <= cloud_cover <= 100

    @pytest.mark.asyncio
    async def test_get_stargazing_conditions(self, client):
        """Test getting stargazing conditions."""
        conditions = await client.get_stargazing_conditions(
            latitude=40.71,
            longitude=-74.01,
        )
        await client.close()

        assert conditions.get("available") is True
        if conditions.get("has_nighttime_data"):
            assert "avg_cloud_cover_percent" in conditions
            assert "min_cloud_cover_percent" in conditions

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close."""
        await client.close()  # Should not raise
