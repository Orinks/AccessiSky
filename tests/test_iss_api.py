"""Tests for ISS API client."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from accessisky.api.iss import ISSClient, ISSPosition, ISSPass


class TestISSPosition:
    """Tests for ISSPosition dataclass."""

    def test_position_creation(self):
        """Test creating an ISS position."""
        pos = ISSPosition(
            latitude=45.0,
            longitude=-93.0,
            altitude=408.0,
            velocity=7.66,
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert pos.latitude == 45.0
        assert pos.longitude == -93.0
        assert pos.altitude == 408.0
        assert pos.velocity == 7.66

    def test_position_str(self):
        """Test string representation of position."""
        pos = ISSPosition(
            latitude=45.5,
            longitude=-93.25,
            altitude=408.0,
            velocity=7.66,
            timestamp=datetime(2026, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert "45.5" in str(pos)
        assert "-93.25" in str(pos)


class TestISSPass:
    """Tests for ISSPass dataclass."""

    def test_pass_creation(self):
        """Test creating an ISS pass prediction."""
        pass_time = ISSPass(
            rise_time=datetime(2026, 1, 30, 18, 30, 0, tzinfo=timezone.utc),
            culmination_time=datetime(2026, 1, 30, 18, 33, 0, tzinfo=timezone.utc),
            set_time=datetime(2026, 1, 30, 18, 36, 0, tzinfo=timezone.utc),
            duration_seconds=360,
            max_elevation=45.0,
            rise_azimuth="NW",
            set_azimuth="SE",
            is_visible=True,
        )
        assert pass_time.duration_seconds == 360
        assert pass_time.max_elevation == 45.0
        assert pass_time.is_visible is True

    def test_pass_duration_minutes(self):
        """Test duration in minutes calculation."""
        pass_time = ISSPass(
            rise_time=datetime(2026, 1, 30, 18, 30, 0, tzinfo=timezone.utc),
            culmination_time=datetime(2026, 1, 30, 18, 33, 0, tzinfo=timezone.utc),
            set_time=datetime(2026, 1, 30, 18, 36, 0, tzinfo=timezone.utc),
            duration_seconds=360,
            max_elevation=45.0,
        )
        assert pass_time.duration_minutes == 6


class TestISSClient:
    """Tests for ISS API client."""

    @pytest.fixture
    def client(self):
        """Create an ISS client for testing."""
        return ISSClient()

    @pytest.mark.asyncio
    async def test_get_current_position(self, client):
        """Test fetching current ISS position."""
        mock_response = {
            "iss_position": {"latitude": "45.0", "longitude": "-93.0"},
            "timestamp": 1706616000,
        }

        with patch.object(client, "_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response
            position = await client.get_current_position()

            assert position is not None
            assert position.latitude == 45.0
            assert position.longitude == -93.0

    @pytest.mark.asyncio
    async def test_get_current_position_error(self, client):
        """Test handling API errors gracefully."""
        with patch.object(client, "_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("API error")
            position = await client.get_current_position()

            assert position is None

    @pytest.mark.asyncio
    async def test_get_passes(self, client):
        """Test fetching ISS pass predictions."""
        mock_response = {
            "passes": [
                {
                    "rise": {"utc_datetime": "2026-01-30T18:30:00+00:00", "azimuth": 315},
                    "culmination": {"utc_datetime": "2026-01-30T18:33:00+00:00", "elevation": 45},
                    "set": {"utc_datetime": "2026-01-30T18:36:00+00:00", "azimuth": 135},
                    "visible": True,
                }
            ]
        }

        with patch.object(client, "_fetch_json", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response
            passes = await client.get_passes(latitude=45.0, longitude=-93.0)

            assert len(passes) == 1
            assert passes[0].max_elevation == 45
            assert passes[0].is_visible is True
