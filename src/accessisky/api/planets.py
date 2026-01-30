"""Planet visibility calculations - local calculations, no API needed.

This uses simplified orbital mechanics to estimate planet positions
and visibility. For accurate predictions, use proper ephemeris data,
but this provides a good approximation for casual observing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum


class PlanetVisibility(Enum):
    """Planet visibility status."""

    NOT_VISIBLE = "Not visible (too close to Sun)"
    MORNING = "Morning sky (before sunrise)"
    EVENING = "Evening sky (after sunset)"
    ALL_NIGHT = "Visible most of the night"


@dataclass
class Planet:
    """Information about a planet."""

    name: str
    orbital_period_days: float  # Sidereal orbital period
    magnitude_range: tuple[float, float]  # Apparent magnitude range (min, max)
    # Orbital elements (simplified)
    semi_major_axis_au: float = 1.0  # AU from Sun
    eccentricity: float = 0.0
    # Epoch for calculations (J2000.0)
    mean_longitude_j2000: float = 0.0  # degrees at J2000.0

    @property
    def is_inner_planet(self) -> bool:
        """Check if planet is inside Earth's orbit."""
        return self.semi_major_axis_au < 1.0


@dataclass
class PlanetInfo:
    """Information about a planet's current visibility."""

    planet: Planet
    visibility: PlanetVisibility
    best_viewing_time: str | None = None
    elongation_degrees: float | None = None  # Angular distance from Sun
    current_magnitude: float | None = None
    is_retrograde: bool = False
    constellation: str | None = None

    @property
    def brightness_description(self) -> str:
        """Get a description of the planet's brightness."""
        if self.current_magnitude is None:
            return "Unknown"
        mag = self.current_magnitude
        if mag < -3:
            return "Very Bright"
        elif mag < -1:
            return "Bright"
        elif mag < 1:
            return "Moderate"
        else:
            return "Dim"

    def __str__(self) -> str:
        vis = self.visibility.value
        if self.best_viewing_time:
            vis = f"{vis} - {self.best_viewing_time}"
        brightness = f", {self.brightness_description}" if self.current_magnitude else ""
        return f"{self.planet.name}: {vis}{brightness}"


# Planet data (simplified orbital elements)
# Data from NASA/JPL Horizons approximations
PLANETS: list[Planet] = [
    Planet(
        name="Mercury",
        orbital_period_days=87.97,
        magnitude_range=(-2.6, 5.7),
        semi_major_axis_au=0.387,
        eccentricity=0.206,
        mean_longitude_j2000=252.25,
    ),
    Planet(
        name="Venus",
        orbital_period_days=224.70,
        magnitude_range=(-4.9, -3.8),
        semi_major_axis_au=0.723,
        eccentricity=0.007,
        mean_longitude_j2000=181.98,
    ),
    Planet(
        name="Mars",
        orbital_period_days=686.98,
        magnitude_range=(-2.9, 1.8),
        semi_major_axis_au=1.524,
        eccentricity=0.093,
        mean_longitude_j2000=355.45,
    ),
    Planet(
        name="Jupiter",
        orbital_period_days=4332.59,
        magnitude_range=(-2.9, -1.6),
        semi_major_axis_au=5.203,
        eccentricity=0.048,
        mean_longitude_j2000=34.40,
    ),
    Planet(
        name="Saturn",
        orbital_period_days=10759.22,
        magnitude_range=(-0.5, 1.5),
        semi_major_axis_au=9.537,
        eccentricity=0.054,
        mean_longitude_j2000=49.94,
    ),
    Planet(
        name="Uranus",
        orbital_period_days=30688.5,
        magnitude_range=(5.3, 5.9),
        semi_major_axis_au=19.19,
        eccentricity=0.047,
        mean_longitude_j2000=313.23,
    ),
    Planet(
        name="Neptune",
        orbital_period_days=60182.0,
        magnitude_range=(7.8, 8.0),
        semi_major_axis_au=30.07,
        eccentricity=0.009,
        mean_longitude_j2000=304.88,
    ),
    Planet(
        name="Earth",  # For internal calculations only
        orbital_period_days=365.25,
        magnitude_range=(0, 0),
        semi_major_axis_au=1.0,
        eccentricity=0.017,
        mean_longitude_j2000=100.46,
    ),
]

# J2000.0 epoch
J2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _days_since_j2000(dt: datetime | date) -> float:
    """Get Julian days since J2000.0 epoch."""
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time().replace(hour=12), tzinfo=timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    delta = dt - J2000
    return delta.total_seconds() / 86400.0


def _mean_longitude(planet: Planet, days: float) -> float:
    """Calculate mean longitude of a planet (simplified)."""
    # Daily motion in degrees
    daily_motion = 360.0 / planet.orbital_period_days
    # Current mean longitude
    longitude = planet.mean_longitude_j2000 + daily_motion * days
    return longitude % 360.0


def _calculate_elongation(planet: Planet, on_date: date) -> float:
    """
    Calculate approximate elongation (angular distance from Sun).
    
    This is a simplified calculation that gives reasonable results
    for casual observing purposes.
    """
    days = _days_since_j2000(on_date)
    
    # Get Earth's longitude
    earth = next(p for p in PLANETS if p.name == "Earth")
    earth_longitude = _mean_longitude(earth, days)
    
    # Get planet's longitude
    planet_longitude = _mean_longitude(planet, days)
    
    # For inner planets, elongation is limited by orbit
    if planet.is_inner_planet:
        # Calculate heliocentric angle
        angle_diff = (planet_longitude - earth_longitude) % 360
        
        # Maximum elongation for inner planets
        max_elongation = math.degrees(math.asin(planet.semi_major_axis_au))
        
        # Approximate current elongation based on orbital position
        # This is simplified - real calculations are more complex
        if angle_diff < 180:
            phase = angle_diff / 180.0
        else:
            phase = (360 - angle_diff) / 180.0
        
        elongation = max_elongation * math.sin(phase * math.pi)
        return abs(elongation)
    
    else:
        # For outer planets, elongation can be up to 180 degrees
        angle_diff = (planet_longitude - earth_longitude) % 360
        
        # Convert to elongation (0-180)
        if angle_diff > 180:
            elongation = 360 - angle_diff
        else:
            elongation = angle_diff
        
        return elongation


def _determine_visibility(planet: Planet, elongation: float) -> tuple[PlanetVisibility, str | None]:
    """
    Determine visibility status based on elongation.
    
    Returns visibility enum and best viewing time description.
    """
    # Planets too close to Sun are not visible
    if elongation < 10:
        return PlanetVisibility.NOT_VISIBLE, None
    
    if planet.is_inner_planet:
        # Inner planets: morning or evening only
        # Need to determine if east or west of Sun
        # This is simplified - we use elongation magnitude only
        if elongation < 18:
            return PlanetVisibility.NOT_VISIBLE, None
        else:
            # Alternate between morning and evening based on orbital position
            # In reality this depends on whether planet is east or west of Sun
            return PlanetVisibility.EVENING, "Look west after sunset"
    else:
        # Outer planets
        if elongation > 150:
            return PlanetVisibility.ALL_NIGHT, "Rises at sunset, sets at sunrise"
        elif elongation > 90:
            return PlanetVisibility.EVENING, "Best in evening, high after sunset"
        elif elongation > 45:
            return PlanetVisibility.MORNING, "Best in morning before sunrise"
        else:
            return PlanetVisibility.MORNING, "Low in morning sky"


def _estimate_magnitude(planet: Planet, elongation: float) -> float:
    """Estimate current apparent magnitude."""
    min_mag, max_mag = planet.magnitude_range
    
    if planet.is_inner_planet:
        # Inner planets are brightest when more illuminated
        # but also when closest to Earth
        # Simplified: brighter when elongation is moderate
        if elongation < 20:
            return max_mag  # Dim when close to Sun
        elif elongation > 40:
            return (min_mag + max_mag) / 2  # Moderate
        else:
            return min_mag  # Brightest at moderate elongation
    else:
        # Outer planets are brightest at opposition (elongation ~180)
        factor = elongation / 180.0
        return max_mag - (max_mag - min_mag) * factor


def get_all_planets() -> list[Planet]:
    """Get list of all planets (excluding Earth)."""
    return [p for p in PLANETS if p.name != "Earth"]


def get_visible_planets(
    on_date: date | None = None,
    min_elongation: float = 15.0,
) -> list[PlanetInfo]:
    """
    Get list of planets visible on a given date.
    
    Args:
        on_date: Date to check (defaults to today)
        min_elongation: Minimum elongation from Sun to be considered visible
    
    Returns:
        List of PlanetInfo for visible planets
    """
    if on_date is None:
        on_date = date.today()
    
    results = []
    
    for planet in get_all_planets():
        elongation = _calculate_elongation(planet, on_date)
        
        if elongation >= min_elongation:
            visibility, viewing_time = _determine_visibility(planet, elongation)
            
            if visibility != PlanetVisibility.NOT_VISIBLE:
                magnitude = _estimate_magnitude(planet, elongation)
                
                results.append(PlanetInfo(
                    planet=planet,
                    visibility=visibility,
                    best_viewing_time=viewing_time,
                    elongation_degrees=round(elongation, 1),
                    current_magnitude=round(magnitude, 1),
                ))
    
    # Sort by brightness (most negative magnitude first)
    results.sort(key=lambda x: x.current_magnitude or 10)
    return results


def get_planet_info(
    name: str,
    on_date: date | None = None,
) -> PlanetInfo | None:
    """
    Get information about a specific planet.
    
    Args:
        name: Planet name (case insensitive)
        on_date: Date to check (defaults to today)
    
    Returns:
        PlanetInfo or None if planet not found
    """
    if on_date is None:
        on_date = date.today()
    
    name_lower = name.lower()
    planet = next((p for p in PLANETS if p.name.lower() == name_lower), None)
    
    if planet is None or planet.name == "Earth":
        return None
    
    elongation = _calculate_elongation(planet, on_date)
    visibility, viewing_time = _determine_visibility(planet, elongation)
    magnitude = _estimate_magnitude(planet, elongation)
    
    return PlanetInfo(
        planet=planet,
        visibility=visibility,
        best_viewing_time=viewing_time,
        elongation_degrees=round(elongation, 1),
        current_magnitude=round(magnitude, 1),
    )


class PlanetClient:
    """Client interface for planet data (for consistency with other API clients)."""

    async def get_all_planets(self) -> list[Planet]:
        """Get all planets."""
        return get_all_planets()

    async def get_visible_planets(
        self,
        on_date: date | None = None,
    ) -> list[PlanetInfo]:
        """Get currently visible planets."""
        return get_visible_planets(on_date)

    async def get_planet_info(
        self,
        name: str,
        on_date: date | None = None,
    ) -> PlanetInfo | None:
        """Get info about a specific planet."""
        return get_planet_info(name, on_date)

    async def close(self) -> None:
        """No-op for API consistency."""
        pass
