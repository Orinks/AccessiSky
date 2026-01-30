"""Tests for geocoding API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from accessisky.api.geocoding import GeocodingClient, GeocodingResult, search_location


def create_mock_response(json_data):
    """Create a mock httpx response."""
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = MagicMock()
    return mock_response


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
        mock_response_data = {
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

        mock_client = AsyncMock()
        mock_client.get.return_value = create_mock_response(mock_response_data)

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value = mock_client
            mock_async_client.return_value.__aexit__.return_value = None

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
        mock_response_data = {"results": []}

        mock_client = AsyncMock()
        mock_client.get.return_value = create_mock_response(mock_response_data)

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value = mock_client
            mock_async_client.return_value.__aexit__.return_value = None

            results = await client.search("xyznonexistent123")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self, client):
        """Test graceful handling of timeout."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value = mock_client
            mock_async_client.return_value.__aexit__.return_value = None

            results = await client.search("New York")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self, client):
        """Test graceful handling of HTTP errors."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock()
        )

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value = mock_client
            mock_async_client.return_value.__aexit__.return_value = None

            results = await client.search("New York")
            assert results == []


class TestSearchLocationFunction:
    """Tests for the convenience search_location function."""

    @pytest.mark.asyncio
    async def test_search_location_function(self):
        """Test the convenience function works."""
        mock_response_data = {
            "results": [
                {
                    "name": "London",
                    "latitude": 51.5074,
                    "longitude": -0.1278,
                    "country": "United Kingdom",
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = create_mock_response(mock_response_data)

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value = mock_client
            mock_async_client.return_value.__aexit__.return_value = None

            results = await search_location("London")

            assert len(results) == 1
            assert results[0].name == "London"
