"""Tests for Tonight's Summary API."""

from unittest.mock import AsyncMock, patch

import pytest

from accessisky.api.tonight import (
    TonightData,
    TonightSummary,
    generate_summary_text,
)


class TestTonightData:
    """Tests for TonightData dataclass."""

    def test_tonight_data_creation(self):
        """Test creating TonightData with minimal data."""
        data = TonightData()

        assert data.moon_phase is None
        assert data.moon_illumination is None
        assert data.iss_passes == []
        assert data.visible_planets == []
        assert data.active_meteor_showers == []
        assert data.aurora_kp is None
        assert data.viewing_score is None
        assert data.cloud_cover_percent is None

    def test_tonight_data_with_values(self):
        """Test creating TonightData with values."""
        data = TonightData(
            moon_phase="Waxing Gibbous",
            moon_illumination=78,
            moon_rise_time="21:30",
            iss_passes=["20:45 - 4 min, max 65°"],
            visible_planets=["Jupiter", "Saturn"],
            active_meteor_showers=["Quadrantids"],
            aurora_kp=3.0,
            viewing_score=72,
            cloud_cover_percent=25,
            summary_text="Tonight's summary...",
        )

        assert data.moon_phase == "Waxing Gibbous"
        assert data.moon_illumination == 78
        assert len(data.visible_planets) == 2
        assert data.aurora_kp == 3.0


class TestGenerateSummaryText:
    """Tests for summary text generation."""

    def test_summary_with_all_data(self):
        """Test generating summary with all data present."""
        data = TonightData(
            moon_phase="Waxing Gibbous",
            moon_illumination=78,
            moon_rise_time="21:30",
            iss_passes=["20:45 for 4 minutes"],
            visible_planets=["Jupiter", "Saturn"],
            active_meteor_showers=["Quadrantids"],
            aurora_kp=2.5,
            viewing_score=72,
            cloud_cover_percent=25,
        )

        summary = generate_summary_text(data)

        assert "Tonight:" in summary
        # Moon phase name should be present
        assert "Waxing Gibbous" in summary
        assert "78%" in summary
        assert "ISS" in summary
        assert "Jupiter" in summary
        assert "Saturn" in summary
        assert "Quadrantids" in summary

    def test_summary_with_minimal_data(self):
        """Test generating summary with minimal data."""
        data = TonightData()

        summary = generate_summary_text(data)

        assert "Tonight:" in summary
        # Should still produce a valid summary

    def test_summary_with_only_moon(self):
        """Test summary with only moon data."""
        data = TonightData(
            moon_phase="Full Moon",
            moon_illumination=100,
        )

        summary = generate_summary_text(data)

        assert "Full Moon" in summary
        assert "100%" in summary

    def test_summary_with_no_iss_passes(self):
        """Test summary when no ISS passes tonight."""
        data = TonightData(
            moon_phase="New Moon",
            moon_illumination=0,
            iss_passes=[],
        )

        summary = generate_summary_text(data)

        # Should not mention ISS or say no passes
        assert "Tonight:" in summary

    def test_summary_with_multiple_planets(self):
        """Test summary with multiple visible planets."""
        data = TonightData(
            visible_planets=["Venus", "Mars", "Jupiter", "Saturn"],
        )

        summary = generate_summary_text(data)

        # Should list planets
        assert "Venus" in summary or "4" in summary or "planets" in summary.lower()

    def test_summary_with_aurora_activity(self):
        """Test summary with high aurora activity."""
        data = TonightData(
            aurora_kp=5.0,
            aurora_activity="Minor Storm",
        )

        summary = generate_summary_text(data)

        assert "aurora" in summary.lower() or "Aurora" in summary or "storm" in summary.lower()

    def test_summary_with_poor_conditions(self):
        """Test summary with poor viewing conditions."""
        data = TonightData(
            viewing_score=20,
            cloud_cover_percent=90,
            viewing_description="Overcast",
        )

        summary = generate_summary_text(data)

        # Should mention poor conditions
        assert (
            "cloud" in summary.lower() or "poor" in summary.lower() or "overcast" in summary.lower()
        )


class TestTonightSummary:
    """Tests for TonightSummary class."""

    @pytest.fixture
    def tonight_summary(self):
        """Create a TonightSummary instance."""
        return TonightSummary()

    def test_init(self, tonight_summary):
        """Test TonightSummary initialization."""
        assert tonight_summary is not None

    @pytest.mark.asyncio
    async def test_get_summary_returns_tonight_data(self, tonight_summary):
        """Test that get_summary returns TonightData."""
        # Mock all the clients
        with (
            patch.object(tonight_summary, "_get_moon_data", new_callable=AsyncMock) as mock_moon,
            patch.object(tonight_summary, "_get_iss_data", new_callable=AsyncMock) as mock_iss,
            patch.object(
                tonight_summary, "_get_planets_data", new_callable=AsyncMock
            ) as mock_planets,
            patch.object(
                tonight_summary, "_get_meteor_data", new_callable=AsyncMock
            ) as mock_meteor,
            patch.object(
                tonight_summary, "_get_aurora_data", new_callable=AsyncMock
            ) as mock_aurora,
            patch.object(
                tonight_summary, "_get_viewing_data", new_callable=AsyncMock
            ) as mock_viewing,
        ):
            mock_moon.return_value = ("Waxing Gibbous", 78, "21:30", "05:30")
            mock_iss.return_value = []
            mock_planets.return_value = ["Jupiter", "Saturn"]
            mock_meteor.return_value = []
            mock_aurora.return_value = (2.0, "Quiet")
            mock_viewing.return_value = (72, 25, "Good")

            result = await tonight_summary.get_summary(latitude=40.0, longitude=-74.0)

            assert isinstance(result, TonightData)
            assert result.moon_phase == "Waxing Gibbous"
            assert result.moon_illumination == 78
            assert result.visible_planets == ["Jupiter", "Saturn"]

    @pytest.mark.asyncio
    async def test_get_summary_handles_api_failures(self, tonight_summary):
        """Test that get_summary handles individual API failures gracefully."""
        with (
            patch.object(tonight_summary, "_get_moon_data", new_callable=AsyncMock) as mock_moon,
            patch.object(tonight_summary, "_get_iss_data", new_callable=AsyncMock) as mock_iss,
            patch.object(
                tonight_summary, "_get_planets_data", new_callable=AsyncMock
            ) as mock_planets,
            patch.object(
                tonight_summary, "_get_meteor_data", new_callable=AsyncMock
            ) as mock_meteor,
            patch.object(
                tonight_summary, "_get_aurora_data", new_callable=AsyncMock
            ) as mock_aurora,
            patch.object(
                tonight_summary, "_get_viewing_data", new_callable=AsyncMock
            ) as mock_viewing,
        ):
            # Some APIs fail
            mock_moon.side_effect = Exception("API error")
            mock_iss.return_value = []
            mock_planets.return_value = ["Jupiter"]
            mock_meteor.side_effect = Exception("Network error")
            mock_aurora.return_value = (1.0, "Quiet")
            mock_viewing.side_effect = Exception("Weather API down")

            result = await tonight_summary.get_summary(latitude=40.0, longitude=-74.0)

            # Should still return valid data with available info
            assert isinstance(result, TonightData)
            assert result.moon_phase is None  # Failed
            assert result.visible_planets == ["Jupiter"]  # Succeeded

    @pytest.mark.asyncio
    async def test_get_summary_generates_text(self, tonight_summary):
        """Test that summary text is generated."""
        with (
            patch.object(tonight_summary, "_get_moon_data", new_callable=AsyncMock) as mock_moon,
            patch.object(tonight_summary, "_get_iss_data", new_callable=AsyncMock) as mock_iss,
            patch.object(
                tonight_summary, "_get_planets_data", new_callable=AsyncMock
            ) as mock_planets,
            patch.object(
                tonight_summary, "_get_meteor_data", new_callable=AsyncMock
            ) as mock_meteor,
            patch.object(
                tonight_summary, "_get_aurora_data", new_callable=AsyncMock
            ) as mock_aurora,
            patch.object(
                tonight_summary, "_get_viewing_data", new_callable=AsyncMock
            ) as mock_viewing,
        ):
            mock_moon.return_value = ("Full Moon", 100, None, None)
            mock_iss.return_value = []
            mock_planets.return_value = []
            mock_meteor.return_value = []
            mock_aurora.return_value = (1.0, "Quiet")
            mock_viewing.return_value = (60, 30, "Fair")

            result = await tonight_summary.get_summary(latitude=40.0, longitude=-74.0)

            assert result.summary_text is not None
            assert len(result.summary_text) > 0
            assert "Tonight:" in result.summary_text

    @pytest.mark.asyncio
    async def test_close(self, tonight_summary):
        """Test closing the client."""
        await tonight_summary.close()
        # Should not raise


class TestTonightSummaryIntegration:
    """Integration tests for TonightSummary (using real calculations, mocked HTTP)."""

    @pytest.mark.asyncio
    async def test_full_summary_generation(self):
        """Test generating a full summary with real calculation logic."""
        summary = TonightSummary()

        try:
            # Use mock for HTTP clients but real calculation logic
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                # Mock HTTP responses to fail - should use fallback calculations
                mock_get.side_effect = Exception("No network")

                result = await summary.get_summary(
                    latitude=40.7128,  # NYC
                    longitude=-74.0060,
                )

                # Should have some data from local calculations
                assert isinstance(result, TonightData)
                assert result.summary_text is not None
        finally:
            await summary.close()
