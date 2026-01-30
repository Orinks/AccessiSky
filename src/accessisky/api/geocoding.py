"""Geocoding API client using Open-Meteo."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass
class GeocodingResult:
    """A geocoding search result."""

    name: str
    latitude: float
    longitude: float
    country: str
    admin1: str | None = None  # State/province
    timezone: str | None = None
    population: int | None = None

    @property
    def display_name(self) -> str:
        """Get a display-friendly name."""
        parts = [self.name]
        if self.admin1:
            parts.append(self.admin1)
        parts.append(self.country)
        return ", ".join(parts)

    def __str__(self) -> str:
        return self.display_name


class GeocodingClient:
    """Client for Open-Meteo geocoding API."""

    def __init__(self, timeout: float = 10.0):
        """Initialize the geocoding client."""
        self.timeout = timeout

    async def search(self, query: str, count: int = 10) -> list[GeocodingResult]:
        """
        Search for locations by name.

        Args:
            query: Location name to search for
            count: Maximum number of results

        Returns:
            List of matching locations
        """
        if not query or not query.strip():
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    GEOCODING_URL,
                    params={
                        "name": query.strip(),
                        "count": count,
                        "language": "en",
                        "format": "json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", []):
                    results.append(
                        GeocodingResult(
                            name=item.get("name", "Unknown"),
                            latitude=item.get("latitude", 0.0),
                            longitude=item.get("longitude", 0.0),
                            country=item.get("country", "Unknown"),
                            admin1=item.get("admin1"),
                            timezone=item.get("timezone"),
                            population=item.get("population"),
                        )
                    )

                return results

        except httpx.TimeoutException:
            logger.error("Geocoding request timed out")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"Geocoding HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return []


async def search_location(query: str, count: int = 10) -> list[GeocodingResult]:
    """
    Convenience function to search for locations.

    Args:
        query: Location name to search for
        count: Maximum number of results

    Returns:
        List of matching locations
    """
    client = GeocodingClient()
    return await client.search(query, count)
