"""Tests for Sun API client."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from accessisky.api.sun import SunClient, SunTimes


class TestSunTimes:
    """Tests for SunTimes dataclass."""

    def test_sun_times_creation(self):
        """Test creating sun times."""
        times = SunTimes(
            date=date(2026, 1, 30),
            sunrise=datetime(2026, 1, 30, 12, 30, 0, tzinfo=timezone.utc),
            sunset=datetime(2026, 1, 30, 23, 15, 0, tzinfo=timezone.utc),
            solar_noon=datetime(2026, 1, 30, 17, 52, 0, tzinfo=timezone.utc),
            day_length_seconds=38700,
            civil_twilight_begin=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            civil_twilight_end=datetime(2026, 1, 30, 23, 45, 0, tzinfo=timezone.utc),
            nautical_twilight_begin=datetime(2026, 1, 30, 11, 30, 0, tzinfo=timezone.utc),
            nautical_twilight_end=datetime(2026, 1, 31, 0, 15, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 1, 30, 11, 0, 0, tzinfo=timezone.utc),
            astronomical_twilight_end=datetime(2026, 1, 31, 0, 45, 0, tzinfo=timezone.utc),
        )
        assert times.date == date(2026, 1, 30)
        assert times.day_length_seconds == 38700

    def test_day_length_property(self):
        """Test day length formatting."""
        times = SunTimes(
            date=date(2026, 1, 30),
            sunrise=datetime(2026, 1, 30, 12, 30, 0, tzinfo=timezone.utc),
            sunset=datetime(2026, 1, 30, 23, 15, 0, tzinfo=timezone.utc),
            solar_noon=datetime(2026, 1, 30, 17, 52, 0, tzinfo=timezone.utc),
            day_length_seconds=38700,  # 10h 45m
            civil_twilight_begin=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            civil_twilight_end=datetime(2026, 1, 30, 23, 45, 0, tzinfo=timezone.utc),
            nautical_twilight_begin=datetime(2026, 1, 30, 11, 30, 0, tzinfo=timezone.utc),
            nautical_twilight_end=datetime(2026, 1, 31, 0, 15, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 1, 30, 11, 0, 0, tzinfo=timezone.utc),
            astronomical_twilight_end=datetime(2026, 1, 31, 0, 45, 0, tzinfo=timezone.utc),
        )
        assert times.day_length == "10h 45m"

    def test_golden_hour_properties(self):
        """Test golden hour calculations."""
        times = SunTimes(
            date=date(2026, 1, 30),
            sunrise=datetime(2026, 1, 30, 7, 0, 0, tzinfo=timezone.utc),
            sunset=datetime(2026, 1, 30, 17, 0, 0, tzinfo=timezone.utc),
            solar_noon=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            day_length_seconds=36000,
            civil_twilight_begin=datetime(2026, 1, 30, 6, 30, 0, tzinfo=timezone.utc),
            civil_twilight_end=datetime(2026, 1, 30, 17, 30, 0, tzinfo=timezone.utc),
            nautical_twilight_begin=datetime(2026, 1, 30, 6, 0, 0, tzinfo=timezone.utc),
            nautical_twilight_end=datetime(2026, 1, 30, 18, 0, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 1, 30, 5, 30, 0, tzinfo=timezone.utc),
            astronomical_twilight_end=datetime(2026, 1, 30, 18, 30, 0, tzinfo=timezone.utc),
        )
        assert times.golden_hour_morning_end.hour == 8
        assert times.golden_hour_evening_start.hour == 16

    def test_str_representation(self):
        """Test string representation."""
        times = SunTimes(
            date=date(2026, 1, 30),
            sunrise=datetime(2026, 1, 30, 7, 30, 0, tzinfo=timezone.utc),
            sunset=datetime(2026, 1, 30, 17, 45, 0, tzinfo=timezone.utc),
            solar_noon=datetime(2026, 1, 30, 12, 37, 0, tzinfo=timezone.utc),
            day_length_seconds=36900,
            civil_twilight_begin=datetime(2026, 1, 30, 7, 0, 0, tzinfo=timezone.utc),
            civil_twilight_end=datetime(2026, 1, 30, 18, 15, 0, tzinfo=timezone.utc),
            nautical_twilight_begin=datetime(2026, 1, 30, 6, 30, 0, tzinfo=timezone.utc),
            nautical_twilight_end=datetime(2026, 1, 30, 18, 45, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 1, 30, 6, 0, 0, tzinfo=timezone.utc),
            astronomical_twilight_end=datetime(2026, 1, 30, 19, 15, 0, tzinfo=timezone.utc),
        )
        s = str(times)
        assert "07:30" in s
        assert "17:45" in s


class TestSunClient:
    """Tests for Sun API client."""

    @pytest.fixture
    def client(self):
        """Create a sun client for testing."""
        return SunClient()

    @pytest.mark.asyncio
    async def test_get_sun_times(self, client):
        """Test fetching sun times."""
        mock_response_data = {
            "results": {
                "sunrise": "2026-01-30T07:30:00+00:00",
                "sunset": "2026-01-30T17:45:00+00:00",
                "solar_noon": "2026-01-30T12:37:00+00:00",
                "day_length": 36900,
                "civil_twilight_begin": "2026-01-30T07:00:00+00:00",
                "civil_twilight_end": "2026-01-30T18:15:00+00:00",
                "nautical_twilight_begin": "2026-01-30T06:30:00+00:00",
                "nautical_twilight_end": "2026-01-30T18:45:00+00:00",
                "astronomical_twilight_begin": "2026-01-30T06:00:00+00:00",
                "astronomical_twilight_end": "2026-01-30T19:15:00+00:00",
            },
            "status": "OK",
        }

        # Create a mock response object (httpx response methods are sync)
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response_data
        mock_response_obj.raise_for_status.return_value = None

        # Create a mock HTTP client where get() is async
        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response_obj

        # Inject the mock client directly
        client._client = mock_http

        times = await client.get_sun_times(45.0, -93.0, date(2026, 1, 30))

        assert times is not None
        assert times.sunrise.hour == 7
        assert times.sunset.hour == 17

    @pytest.mark.asyncio
    async def test_get_sun_times_error(self, client):
        """Test handling API errors gracefully."""
        mock_http = AsyncMock()
        mock_http.get.side_effect = Exception("API error")
        client._client = mock_http

        times = await client.get_sun_times(45.0, -93.0)
        assert times is None

    @pytest.mark.asyncio
    async def test_get_sun_times_api_error_status(self, client):
        """Test handling API error status."""
        mock_response_data = {"status": "INVALID_REQUEST"}

        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response_data
        mock_response_obj.raise_for_status.return_value = None

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response_obj
        client._client = mock_http

        times = await client.get_sun_times(999.0, 999.0)
        assert times is None
