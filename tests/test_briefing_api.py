"""Tests for Daily Briefing API."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from accessisky.api.briefing import (
    DailyBriefing,
    DailyBriefingData,
    SpaceWeatherSummary,
    generate_briefing_text,
)


class TestDailyBriefingData:
    """Tests for DailyBriefingData dataclass."""

    def test_daily_briefing_data_creation(self):
        """Test creating DailyBriefingData with minimal data."""
        data = DailyBriefingData()

        assert data.date is None
        assert data.sunrise is None
        assert data.sunset is None
        assert data.day_length is None
        assert data.moon_phase is None
        assert data.moon_illumination is None
        assert data.moon_rise is None
        assert data.moon_set is None
        assert data.iss_passes == []
        assert data.visible_planets == []
        assert data.active_meteor_showers == []
        assert data.eclipse_today is None
        assert data.space_weather is None
        assert data.summary_text is None

    def test_daily_briefing_data_with_values(self):
        """Test creating DailyBriefingData with values."""
        space_weather = SpaceWeatherSummary(
            kp_current=2.0,
            kp_24h_max=3.0,
            activity_level="Quiet",
            solar_wind_speed=400.0,
            aurora_visibility="High latitudes only",
        )

        data = DailyBriefingData(
            date=date(2026, 1, 30),
            sunrise="07:15",
            sunset="17:30",
            day_length="10h 15m",
            moon_phase="Waxing Gibbous",
            moon_illumination=78,
            moon_rise="14:30",
            moon_set="03:45",
            iss_passes=["08:15 (daytime)", "20:45 (visible)"],
            visible_planets=["Venus", "Jupiter", "Saturn"],
            active_meteor_showers=["Quadrantids"],
            eclipse_today=None,
            space_weather=space_weather,
        )

        assert data.date == date(2026, 1, 30)
        assert data.sunrise == "07:15"
        assert data.sunset == "17:30"
        assert data.moon_phase == "Waxing Gibbous"
        assert len(data.iss_passes) == 2
        assert len(data.visible_planets) == 3
        assert data.space_weather.kp_current == 2.0


class TestSpaceWeatherSummary:
    """Tests for SpaceWeatherSummary dataclass."""

    def test_space_weather_creation(self):
        """Test creating SpaceWeatherSummary."""
        summary = SpaceWeatherSummary(
            kp_current=5.0,
            kp_24h_max=6.0,
            activity_level="Minor Storm",
            solar_wind_speed=600.0,
            aurora_visibility="Visible at 55° latitude and above",
        )

        assert summary.kp_current == 5.0
        assert summary.kp_24h_max == 6.0
        assert summary.activity_level == "Minor Storm"
        assert summary.solar_wind_speed == 600.0

    def test_space_weather_minimal(self):
        """Test SpaceWeatherSummary with minimal data."""
        summary = SpaceWeatherSummary()

        assert summary.kp_current is None
        assert summary.activity_level is None


class TestGenerateBriefingText:
    """Tests for briefing text generation."""

    def test_briefing_with_all_data(self):
        """Test generating briefing with all data present."""
        data = DailyBriefingData(
            date=date(2026, 1, 30),
            sunrise="07:15",
            sunset="17:30",
            day_length="10h 15m",
            moon_phase="Waxing Gibbous",
            moon_illumination=78,
            moon_rise="14:30",
            moon_set="03:45",
            iss_passes=["08:15 (daytime)", "20:45 (visible)"],
            visible_planets=["Venus", "Jupiter"],
            active_meteor_showers=["Quadrantids"],
            space_weather=SpaceWeatherSummary(
                kp_current=2.0,
                activity_level="Quiet",
            ),
        )

        briefing = generate_briefing_text(data)

        assert "January 30" in briefing or "2026-01-30" in briefing
        assert "07:15" in briefing
        assert "17:30" in briefing
        assert "Waxing Gibbous" in briefing
        assert "ISS" in briefing
        assert "Venus" in briefing or "Jupiter" in briefing
        assert "Quadrantids" in briefing

    def test_briefing_with_minimal_data(self):
        """Test generating briefing with minimal data."""
        data = DailyBriefingData(date=date(2026, 1, 30))

        briefing = generate_briefing_text(data)

        assert len(briefing) > 0
        assert "January 30" in briefing or "2026-01-30" in briefing

    def test_briefing_with_eclipse(self):
        """Test briefing includes eclipse when present."""
        data = DailyBriefingData(
            date=date(2026, 8, 12),
            eclipse_today="Total Solar Eclipse visible from Iceland, Greenland, and Spain",
        )

        briefing = generate_briefing_text(data)

        assert "eclipse" in briefing.lower() or "Eclipse" in briefing

    def test_briefing_with_active_space_weather(self):
        """Test briefing includes active space weather."""
        data = DailyBriefingData(
            date=date(2026, 1, 30),
            space_weather=SpaceWeatherSummary(
                kp_current=5.0,
                kp_24h_max=6.0,
                activity_level="Minor Storm",
                aurora_visibility="Visible at 55° latitude and above",
            ),
        )

        briefing = generate_briefing_text(data)

        # Should mention storm or aurora
        assert (
            "storm" in briefing.lower()
            or "aurora" in briefing.lower()
            or "geomagnetic" in briefing.lower()
        )

    def test_briefing_with_no_iss_passes(self):
        """Test briefing when no ISS passes."""
        data = DailyBriefingData(
            date=date(2026, 1, 30),
            sunrise="07:15",
            sunset="17:30",
            iss_passes=[],
        )

        briefing = generate_briefing_text(data)

        # Should still be valid, may or may not mention ISS
        assert "07:15" in briefing
        assert "17:30" in briefing


class TestDailyBriefing:
    """Tests for DailyBriefing class."""

    @pytest.fixture
    def briefing_client(self):
        """Create a DailyBriefing instance."""
        return DailyBriefing()

    def test_init(self, briefing_client):
        """Test DailyBriefing initialization."""
        assert briefing_client is not None

    @pytest.mark.asyncio
    async def test_get_briefing_returns_data(self, briefing_client):
        """Test that get_briefing returns DailyBriefingData."""
        with (
            patch.object(briefing_client, "_get_sun_data", new_callable=AsyncMock) as mock_sun,
            patch.object(briefing_client, "_get_moon_data", new_callable=AsyncMock) as mock_moon,
            patch.object(briefing_client, "_get_iss_data", new_callable=AsyncMock) as mock_iss,
            patch.object(
                briefing_client, "_get_planets_data", new_callable=AsyncMock
            ) as mock_planets,
            patch.object(
                briefing_client, "_get_meteor_data", new_callable=AsyncMock
            ) as mock_meteor,
            patch.object(
                briefing_client, "_get_eclipse_data", new_callable=AsyncMock
            ) as mock_eclipse,
            patch.object(
                briefing_client, "_get_space_weather_data", new_callable=AsyncMock
            ) as mock_weather,
        ):
            mock_sun.return_value = ("07:15", "17:30", "10h 15m")
            mock_moon.return_value = ("Waxing Gibbous", 78, "14:30", "03:45")
            mock_iss.return_value = ["20:45 (visible)"]
            mock_planets.return_value = ["Jupiter", "Saturn"]
            mock_meteor.return_value = []
            mock_eclipse.return_value = None
            mock_weather.return_value = SpaceWeatherSummary(kp_current=2.0, activity_level="Quiet")

            result = await briefing_client.get_briefing(
                latitude=40.0, longitude=-74.0, target_date=date(2026, 1, 30)
            )

            assert isinstance(result, DailyBriefingData)
            assert result.sunrise == "07:15"
            assert result.sunset == "17:30"
            assert result.moon_phase == "Waxing Gibbous"
            assert result.visible_planets == ["Jupiter", "Saturn"]

    @pytest.mark.asyncio
    async def test_get_briefing_handles_api_failures(self, briefing_client):
        """Test that get_briefing handles individual API failures gracefully."""
        with (
            patch.object(briefing_client, "_get_sun_data", new_callable=AsyncMock) as mock_sun,
            patch.object(briefing_client, "_get_moon_data", new_callable=AsyncMock) as mock_moon,
            patch.object(briefing_client, "_get_iss_data", new_callable=AsyncMock) as mock_iss,
            patch.object(
                briefing_client, "_get_planets_data", new_callable=AsyncMock
            ) as mock_planets,
            patch.object(
                briefing_client, "_get_meteor_data", new_callable=AsyncMock
            ) as mock_meteor,
            patch.object(
                briefing_client, "_get_eclipse_data", new_callable=AsyncMock
            ) as mock_eclipse,
            patch.object(
                briefing_client, "_get_space_weather_data", new_callable=AsyncMock
            ) as mock_weather,
        ):
            # Some APIs fail
            mock_sun.side_effect = Exception("API error")
            mock_moon.return_value = ("Full Moon", 100, None, None)
            mock_iss.side_effect = Exception("Network error")
            mock_planets.return_value = ["Jupiter"]
            mock_meteor.side_effect = Exception("Timeout")
            mock_eclipse.return_value = None
            mock_weather.side_effect = Exception("NOAA down")

            result = await briefing_client.get_briefing(
                latitude=40.0, longitude=-74.0, target_date=date(2026, 1, 30)
            )

            # Should still return valid data with available info
            assert isinstance(result, DailyBriefingData)
            assert result.sunrise is None  # Failed
            assert result.moon_phase == "Full Moon"  # Succeeded
            assert result.visible_planets == ["Jupiter"]  # Succeeded

    @pytest.mark.asyncio
    async def test_get_briefing_generates_text(self, briefing_client):
        """Test that summary text is generated."""
        with (
            patch.object(briefing_client, "_get_sun_data", new_callable=AsyncMock) as mock_sun,
            patch.object(briefing_client, "_get_moon_data", new_callable=AsyncMock) as mock_moon,
            patch.object(briefing_client, "_get_iss_data", new_callable=AsyncMock) as mock_iss,
            patch.object(
                briefing_client, "_get_planets_data", new_callable=AsyncMock
            ) as mock_planets,
            patch.object(
                briefing_client, "_get_meteor_data", new_callable=AsyncMock
            ) as mock_meteor,
            patch.object(
                briefing_client, "_get_eclipse_data", new_callable=AsyncMock
            ) as mock_eclipse,
            patch.object(
                briefing_client, "_get_space_weather_data", new_callable=AsyncMock
            ) as mock_weather,
        ):
            mock_sun.return_value = ("07:15", "17:30", "10h 15m")
            mock_moon.return_value = ("Full Moon", 100, None, None)
            mock_iss.return_value = []
            mock_planets.return_value = []
            mock_meteor.return_value = []
            mock_eclipse.return_value = None
            mock_weather.return_value = None

            result = await briefing_client.get_briefing(
                latitude=40.0, longitude=-74.0, target_date=date(2026, 1, 30)
            )

            assert result.summary_text is not None
            assert len(result.summary_text) > 0

    @pytest.mark.asyncio
    async def test_close(self, briefing_client):
        """Test closing the client."""
        await briefing_client.close()
        # Should not raise


class TestDailyBriefingIntegration:
    """Integration tests for DailyBriefing."""

    @pytest.mark.asyncio
    async def test_full_briefing_generation(self):
        """Test generating a full briefing with mocked HTTP."""
        briefing = DailyBriefing()

        try:
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                # Mock HTTP responses to fail - should use fallback calculations
                mock_get.side_effect = Exception("No network")

                result = await briefing.get_briefing(
                    latitude=40.7128,  # NYC
                    longitude=-74.0060,
                    target_date=date(2026, 1, 30),
                )

                # Should have some data from local calculations
                assert isinstance(result, DailyBriefingData)
                assert result.summary_text is not None
                assert result.date == date(2026, 1, 30)
        finally:
            await briefing.close()

    @pytest.mark.asyncio
    async def test_briefing_for_specific_date(self):
        """Test that briefing respects target_date."""
        briefing = DailyBriefing()

        try:
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = Exception("No network")

                future_date = date(2026, 8, 12)  # Date of a solar eclipse
                result = await briefing.get_briefing(
                    latitude=40.0,
                    longitude=-74.0,
                    target_date=future_date,
                )

                assert result.date == future_date
        finally:
            await briefing.close()


class TestBriefingAsDict:
    """Tests for dict export functionality."""

    def test_as_dict_complete(self):
        """Test converting DailyBriefingData to dict."""
        data = DailyBriefingData(
            date=date(2026, 1, 30),
            sunrise="07:15",
            sunset="17:30",
            day_length="10h 15m",
            moon_phase="Full Moon",
            moon_illumination=100,
            iss_passes=["20:45"],
            visible_planets=["Jupiter"],
        )

        result = data.as_dict()

        assert isinstance(result, dict)
        assert result["date"] == "2026-01-30"
        assert result["sun"]["sunrise"] == "07:15"
        assert result["sun"]["sunset"] == "17:30"
        assert result["moon"]["phase"] == "Full Moon"
        assert result["moon"]["illumination"] == 100
        assert "Jupiter" in result["planets"]

    def test_as_dict_minimal(self):
        """Test as_dict with minimal data."""
        data = DailyBriefingData(date=date(2026, 1, 30))

        result = data.as_dict()

        assert result["date"] == "2026-01-30"
        assert result["sun"]["sunrise"] is None
        assert result["moon"]["phase"] is None
