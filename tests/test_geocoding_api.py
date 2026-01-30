"""Tests for geocoding API client."""

from unittest.mock import AsyncMock, patch

import pytest

from accessisky.api.geocoding import GeocodingClient, GeocodingResult, search_location


class TestGeocodingResult:
    """Tests for GeocodingResult dataclass."""

    def test_result_creation(self):
        """Test creating a geocoding result."""
        result = GeocodingResult(
            name="New York",
            latitude=40.7128,
            longitude=-74.0060,
            country="United States",
            admin1="New York",
            timezone="America/New_York",
            population=8804190,
        )
        assert result.name == "New York"
        assert result.latitude == 40.7128
        assert result.longitude == -74.0060
        assert result.country == "United States"

    def test_display_name_with_admin1(self):
        """Test display name includes state/province."""
        result = GeocodingResult(
            name="New York",
            latitude=40.7128,
            longitude=-74.0060,
            country="United States",
            admin1="New York",
        )
        assert result.display_name == "New York, New York, United States"

    def test_display_name_without_admin1(self):
        """Test display name without state/province."""
        result = GeocodingResult(
            name="London",
            latitude=51.5074,
            longitude=-0.1278,
            country="United Kingdom",
            admin1=None,
        )
        assert result.display_name == "London, United Kingdom"

    def test_str_returns_display_name(self):
        """Test string representation."""
        result = GeocodingResult(
            name="Paris",
            latitude=48.8566,
            longitude=2.3522,
            country="France",
        )
        assert str(result) == "Paris, France"


class TestGeocodingClient:
    """Tests for GeocodingClient."""

    @pytest.fixture
    def client(self):
        """Create a geocoding client for testing."""
        return GeocodingClient()

    @pytest.mark.asyncio
    async def test_search_returns_results(self, client):
        """Test search returns parsed results."""
        mock_response = {
            "results": [
                {
                    "name": "New York",
                    "latitude": 40.7128,
                    "longitude": -74.006,
                    "country": "United States",
                    "admin1": "New York",
                    "timezone": "America/New_York",
                    "population": 8804190,
                }
            ]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            results = await client.search("New York")

            assert len(results) == 1
            assert results[0].name == "New York"
            assert results[0].latitude == 40.7128

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_empty(self, client):
        """Test empty query returns empty results."""
        results = await client.search("")
        assert results == []

        results = await client.search("   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_no_results(self, client):
        """Test handling when API returns no results."""
        mock_response = {"results": []}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            results = await client.search("xyznonexistent123")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self, client):
        """Test graceful handling of timeout."""
        import httpx

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timeout")

            results = await client.search("New York")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self, client):
        """Test graceful handling of HTTP errors."""
        import httpx

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError("error", request=None, response=None)

            results = await client.search("New York")
            assert results == []


class TestSearchLocationFunction:
    """Tests for the convenience search_location function."""

    @pytest.mark.asyncio
    async def test_search_location_function(self):
        """Test the convenience function works."""
        mock_response = {
            "results": [
                {
                    "name": "London",
                    "latitude": 51.5074,
                    "longitude": -0.1278,
                    "country": "United Kingdom",
                }
            ]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            results = await search_location("London")

            assert len(results) == 1
            assert results[0].name == "London"
