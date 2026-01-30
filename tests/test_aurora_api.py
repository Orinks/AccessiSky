"""Tests for Aurora/Space Weather API client."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from accessisky.api.aurora import (
    AuroraClient,
    AuroraForecast,
    GeomagActivity,
    KpIndex,
    SolarWind,
    _activity_description,
    _kp_to_activity,
)


class TestGeomagActivity:
    """Tests for geomagnetic activity classification."""

    def test_kp_to_activity_quiet(self):
        """Test quiet conditions classification."""
        assert _kp_to_activity(0) == GeomagActivity.QUIET
        assert _kp_to_activity(1) == GeomagActivity.QUIET
        assert _kp_to_activity(1.5) == GeomagActivity.QUIET

    def test_kp_to_activity_unsettled(self):
        """Test unsettled conditions classification."""
        assert _kp_to_activity(2) == GeomagActivity.UNSETTLED
        assert _kp_to_activity(3) == GeomagActivity.UNSETTLED
        assert _kp_to_activity(3.5) == GeomagActivity.UNSETTLED

    def test_kp_to_activity_active(self):
        """Test active conditions classification."""
        assert _kp_to_activity(4) == GeomagActivity.ACTIVE
        assert _kp_to_activity(4.5) == GeomagActivity.ACTIVE

    def test_kp_to_activity_storms(self):
        """Test storm classifications."""
        assert _kp_to_activity(5) == GeomagActivity.MINOR_STORM
        assert _kp_to_activity(6) == GeomagActivity.MODERATE_STORM
        assert _kp_to_activity(7) == GeomagActivity.STRONG_STORM
        assert _kp_to_activity(8) == GeomagActivity.SEVERE_STORM
        assert _kp_to_activity(9) == GeomagActivity.EXTREME_STORM

    def test_activity_description(self):
        """Test activity descriptions are provided."""
        for activity in GeomagActivity:
            desc = _activity_description(activity)
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestKpIndex:
    """Tests for KpIndex dataclass."""

    def test_kp_index_creation(self):
        """Test creating Kp index."""
        kp = KpIndex(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            kp=3.5,
            activity=GeomagActivity.UNSETTLED,
        )
        assert kp.kp == 3.5
        assert kp.activity == GeomagActivity.UNSETTLED

    def test_kp_index_description(self):
        """Test Kp index description property."""
        kp = KpIndex(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            kp=5.0,
            activity=GeomagActivity.MINOR_STORM,
        )
        assert "G1" in kp.description or "storm" in kp.description.lower()

    def test_kp_index_str(self):
        """Test string representation."""
        kp = KpIndex(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            kp=4.0,
            activity=GeomagActivity.ACTIVE,
        )
        s = str(kp)
        assert "4.0" in s
        assert "ACTIVE" in s


class TestAuroraForecast:
    """Tests for AuroraForecast dataclass."""

    def test_aurora_forecast_creation(self):
        """Test creating aurora forecast."""
        forecast = AuroraForecast(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            kp_current=3.0,
            kp_24h_max=5.0,
            activity=GeomagActivity.MINOR_STORM,
            hemisphere_power_gw=50.0,
            visibility_latitude=55.0,
        )
        assert forecast.kp_current == 3.0
        assert forecast.kp_24h_max == 5.0
        assert forecast.visibility_latitude == 55.0

    def test_can_see_aurora_high_lat(self):
        """Test visibility description for high latitude."""
        forecast = AuroraForecast(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            kp_current=2.0,
            kp_24h_max=2.0,
            activity=GeomagActivity.UNSETTLED,
            hemisphere_power_gw=None,
            visibility_latitude=65.0,
        )
        assert "far northern" in forecast.can_see_aurora.lower()

    def test_can_see_aurora_mid_lat(self):
        """Test visibility description for mid latitude."""
        forecast = AuroraForecast(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            kp_current=6.0,
            kp_24h_max=6.0,
            activity=GeomagActivity.MODERATE_STORM,
            hemisphere_power_gw=None,
            visibility_latitude=50.0,
        )
        vis = forecast.can_see_aurora.lower()
        assert "northern us" in vis or "uk" in vis or "europe" in vis

    def test_str_representation(self):
        """Test string representation."""
        forecast = AuroraForecast(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            kp_current=4.0,
            kp_24h_max=5.0,
            activity=GeomagActivity.MINOR_STORM,
            hemisphere_power_gw=None,
            visibility_latitude=55.0,
        )
        s = str(forecast)
        assert "4.0" in s
        assert "5.0" in s


class TestSolarWind:
    """Tests for SolarWind dataclass."""

    def test_solar_wind_creation(self):
        """Test creating solar wind data."""
        sw = SolarWind(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            speed_km_s=450.0,
            density_p_cm3=5.0,
            temperature_k=100000.0,
        )
        assert sw.speed_km_s == 450.0
        assert sw.density_p_cm3 == 5.0

    def test_is_elevated_normal(self):
        """Test normal solar wind is not elevated."""
        sw = SolarWind(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            speed_km_s=400.0,
            density_p_cm3=5.0,
            temperature_k=100000.0,
        )
        assert not sw.is_elevated

    def test_is_elevated_high_speed(self):
        """Test high speed solar wind is elevated."""
        sw = SolarWind(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            speed_km_s=600.0,
            density_p_cm3=5.0,
            temperature_k=100000.0,
        )
        assert sw.is_elevated

    def test_is_elevated_high_density(self):
        """Test high density solar wind is elevated."""
        sw = SolarWind(
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
            speed_km_s=400.0,
            density_p_cm3=15.0,
            temperature_k=100000.0,
        )
        assert sw.is_elevated


class TestAuroraClient:
    """Tests for Aurora API client."""

    @pytest.fixture
    def client(self):
        """Create an aurora client for testing."""
        return AuroraClient()

    @pytest.mark.asyncio
    async def test_get_current_kp(self, client):
        """Test fetching current Kp index."""
        mock_response_data = [
            ["time_tag", "Kp", "Kp_fraction", "a_running", "station_count"],
            ["2026-01-30 03:00:00.000", "3", "3.33", "15", "8"],
        ]

        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response_data
        mock_response_obj.raise_for_status.return_value = None

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response_obj
        client._client = mock_http

        kp = await client.get_current_kp()

        assert kp is not None
        assert kp.kp == 3.0
        assert kp.activity == GeomagActivity.UNSETTLED

    @pytest.mark.asyncio
    async def test_get_current_kp_error(self, client):
        """Test handling API errors gracefully."""
        mock_http = AsyncMock()
        mock_http.get.side_effect = Exception("API error")
        client._client = mock_http

        kp = await client.get_current_kp()
        assert kp is None

    @pytest.mark.asyncio
    async def test_get_solar_wind(self, client):
        """Test fetching solar wind data."""
        mock_response_data = [
            ["time_tag", "density", "speed", "temperature"],
            ["2026-01-30 12:00:00.000", "5.5", "450", "100000"],
        ]

        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response_data
        mock_response_obj.raise_for_status.return_value = None

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response_obj
        client._client = mock_http

        sw = await client.get_solar_wind()

        assert sw is not None
        assert sw.speed_km_s == 450.0
        assert sw.density_p_cm3 == 5.5

    @pytest.mark.asyncio
    async def test_get_kp_forecast(self, client):
        """Test fetching Kp forecast."""
        mock_response_data = [
            ["time_tag", "Kp", "observed", "noaa_scale"],
            ["2026-01-30 06:00:00.000", "3", "estimated", "G0"],
            ["2026-01-30 09:00:00.000", "4", "estimated", "G0"],
        ]

        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response_data
        mock_response_obj.raise_for_status.return_value = None

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response_obj
        client._client = mock_http

        forecasts = await client.get_kp_forecast()

        assert len(forecasts) == 2
        assert forecasts[0].kp == 3.0
        assert forecasts[1].kp == 4.0
