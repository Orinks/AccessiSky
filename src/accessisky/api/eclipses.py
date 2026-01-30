"""Eclipse calendar with static data for upcoming eclipses.

Data sourced from NASA Eclipse website and astronomical almanacs.
Covers eclipses from 2025-2030.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class EclipseType(Enum):
    """Types of eclipses."""

    TOTAL_SOLAR = "Total Solar Eclipse"
    PARTIAL_SOLAR = "Partial Solar Eclipse"
    ANNULAR_SOLAR = "Annular Solar Eclipse"
    HYBRID_SOLAR = "Hybrid Solar Eclipse"
    TOTAL_LUNAR = "Total Lunar Eclipse"
    PARTIAL_LUNAR = "Partial Lunar Eclipse"
    PENUMBRAL_LUNAR = "Penumbral Lunar Eclipse"

    @property
    def is_solar(self) -> bool:
        """Check if this is a solar eclipse."""
        return "Solar" in self.value

    @property
    def is_lunar(self) -> bool:
        """Check if this is a lunar eclipse."""
        return "Lunar" in self.value

    @property
    def emoji(self) -> str:
        """Get emoji for eclipse type."""
        if self.is_solar:
            return "🌑"  # New moon for solar
        else:
            return "🌕"  # Full moon for lunar


@dataclass
class Eclipse:
    """Information about an eclipse."""

    eclipse_type: EclipseType
    date: date
    max_time: datetime  # Time of maximum eclipse (UTC)
    duration_minutes: float | None = None  # Duration of totality/annularity
    visibility_regions: list[str] = field(default_factory=list)
    magnitude: float | None = None  # Eclipse magnitude
    saros: int | None = None  # Saros cycle number
    gamma: float | None = None  # Gamma value for solar eclipses
    notes: str | None = None

    def is_visible_from(self, region: str) -> bool:
        """Check if eclipse is visible from a region."""
        region_lower = region.lower()
        return any(region_lower in r.lower() for r in self.visibility_regions)

    def __str__(self) -> str:
        type_str = self.eclipse_type.value
        date_str = self.date.strftime("%Y-%m-%d")
        time_str = self.max_time.strftime("%H:%M UTC")
        regions = ", ".join(self.visibility_regions[:3]) if self.visibility_regions else "Various"

        duration_str = ""
        if self.duration_minutes:
            mins = int(self.duration_minutes)
            secs = int((self.duration_minutes - mins) * 60)
            duration_str = f" ({mins}m {secs}s)"

        return f"{self.eclipse_type.emoji} {type_str} on {date_str} at {time_str}{duration_str} - Visible: {regions}"


# Eclipse data from 2025-2030
# Source: NASA Eclipse website (eclipse.gsfc.nasa.gov)
ECLIPSES: list[Eclipse] = [
    # 2025
    Eclipse(
        eclipse_type=EclipseType.TOTAL_LUNAR,
        date=date(2025, 3, 14),
        max_time=datetime(2025, 3, 14, 6, 58, tzinfo=timezone.utc),
        duration_minutes=65,
        visibility_regions=["Americas", "Europe", "Africa", "Pacific"],
        magnitude=1.178,
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_SOLAR,
        date=date(2025, 3, 29),
        max_time=datetime(2025, 3, 29, 10, 47, tzinfo=timezone.utc),
        visibility_regions=["Northwest Africa", "Europe", "Russia"],
        magnitude=0.938,
    ),
    Eclipse(
        eclipse_type=EclipseType.TOTAL_LUNAR,
        date=date(2025, 9, 7),
        max_time=datetime(2025, 9, 7, 18, 11, tzinfo=timezone.utc),
        duration_minutes=82,
        visibility_regions=["Europe", "Africa", "Asia", "Australia"],
        magnitude=1.362,
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_SOLAR,
        date=date(2025, 9, 21),
        max_time=datetime(2025, 9, 21, 19, 42, tzinfo=timezone.utc),
        visibility_regions=["Antarctica", "New Zealand", "Australia"],
        magnitude=0.855,
    ),
    # 2026
    Eclipse(
        eclipse_type=EclipseType.PENUMBRAL_LUNAR,
        date=date(2026, 3, 3),
        max_time=datetime(2026, 3, 3, 11, 33, tzinfo=timezone.utc),
        visibility_regions=["Asia", "Australia", "Pacific", "Americas"],
        magnitude=0.969,
    ),
    Eclipse(
        eclipse_type=EclipseType.ANNULAR_SOLAR,
        date=date(2026, 2, 17),
        max_time=datetime(2026, 2, 17, 12, 13, tzinfo=timezone.utc),
        duration_minutes=2.2,
        visibility_regions=["Antarctica", "Southern South America"],
        magnitude=0.963,
    ),
    Eclipse(
        eclipse_type=EclipseType.TOTAL_SOLAR,
        date=date(2026, 8, 12),
        max_time=datetime(2026, 8, 12, 17, 46, tzinfo=timezone.utc),
        duration_minutes=2.3,
        visibility_regions=["Arctic", "Greenland", "Iceland", "Spain"],
        magnitude=1.039,
        notes="Visible from parts of Spain, Iceland and Greenland",
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_LUNAR,
        date=date(2026, 8, 28),
        max_time=datetime(2026, 8, 28, 4, 13, tzinfo=timezone.utc),
        visibility_regions=["Americas", "Europe", "Africa"],
        magnitude=0.930,
    ),
    # 2027
    Eclipse(
        eclipse_type=EclipseType.PENUMBRAL_LUNAR,
        date=date(2027, 2, 20),
        max_time=datetime(2027, 2, 20, 23, 13, tzinfo=timezone.utc),
        visibility_regions=["Americas", "Europe", "Africa"],
        magnitude=0.928,
    ),
    Eclipse(
        eclipse_type=EclipseType.ANNULAR_SOLAR,
        date=date(2027, 2, 6),
        max_time=datetime(2027, 2, 6, 16, 0, tzinfo=timezone.utc),
        duration_minutes=7.5,
        visibility_regions=["South America", "Antarctica", "Africa"],
        magnitude=0.928,
    ),
    Eclipse(
        eclipse_type=EclipseType.TOTAL_SOLAR,
        date=date(2027, 8, 2),
        max_time=datetime(2027, 8, 2, 10, 7, tzinfo=timezone.utc),
        duration_minutes=6.4,
        visibility_regions=[
            "Spain",
            "Morocco",
            "Algeria",
            "Libya",
            "Egypt",
            "Saudi Arabia",
            "Yemen",
        ],
        magnitude=1.079,
        notes="One of the best total solar eclipses of the century - crosses Mediterranean",
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_LUNAR,
        date=date(2027, 8, 17),
        max_time=datetime(2027, 8, 17, 7, 12, tzinfo=timezone.utc),
        visibility_regions=["Americas", "Europe", "Africa", "Asia"],
        magnitude=0.100,
    ),
    # 2028
    Eclipse(
        eclipse_type=EclipseType.TOTAL_LUNAR,
        date=date(2028, 1, 12),
        max_time=datetime(2028, 1, 12, 4, 13, tzinfo=timezone.utc),
        duration_minutes=71,
        visibility_regions=["Americas", "Europe", "Africa"],
        magnitude=1.063,
    ),
    Eclipse(
        eclipse_type=EclipseType.ANNULAR_SOLAR,
        date=date(2028, 1, 26),
        max_time=datetime(2028, 1, 26, 15, 8, tzinfo=timezone.utc),
        duration_minutes=10.3,
        visibility_regions=["South America", "Antarctica"],
        magnitude=0.921,
    ),
    Eclipse(
        eclipse_type=EclipseType.TOTAL_LUNAR,
        date=date(2028, 7, 6),
        max_time=datetime(2028, 7, 6, 18, 19, tzinfo=timezone.utc),
        duration_minutes=104,
        visibility_regions=["Americas", "Europe", "Africa", "Asia"],
        magnitude=1.399,
        notes="Longest total lunar eclipse until 2123",
    ),
    Eclipse(
        eclipse_type=EclipseType.TOTAL_SOLAR,
        date=date(2028, 7, 22),
        max_time=datetime(2028, 7, 22, 2, 55, tzinfo=timezone.utc),
        duration_minutes=5.1,
        visibility_regions=["Australia", "New Zealand"],
        magnitude=1.056,
    ),
    # 2029
    Eclipse(
        eclipse_type=EclipseType.PENUMBRAL_LUNAR,
        date=date(2029, 1, 1),
        max_time=datetime(2029, 1, 1, 0, 37, tzinfo=timezone.utc),
        visibility_regions=["Americas", "Europe", "Africa"],
        magnitude=0.090,
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_SOLAR,
        date=date(2029, 1, 14),
        max_time=datetime(2029, 1, 14, 17, 13, tzinfo=timezone.utc),
        visibility_regions=["North America", "Central America"],
        magnitude=0.871,
    ),
    Eclipse(
        eclipse_type=EclipseType.TOTAL_LUNAR,
        date=date(2029, 6, 26),
        max_time=datetime(2029, 6, 26, 3, 22, tzinfo=timezone.utc),
        duration_minutes=70,
        visibility_regions=["Americas", "Europe", "Africa"],
        magnitude=1.177,
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_SOLAR,
        date=date(2029, 7, 11),
        max_time=datetime(2029, 7, 11, 15, 36, tzinfo=timezone.utc),
        visibility_regions=["South America"],
        magnitude=0.230,
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_LUNAR,
        date=date(2029, 12, 20),
        max_time=datetime(2029, 12, 20, 22, 42, tzinfo=timezone.utc),
        visibility_regions=["Americas", "Europe", "Africa", "Asia"],
        magnitude=0.965,
    ),
    # 2030
    Eclipse(
        eclipse_type=EclipseType.ANNULAR_SOLAR,
        date=date(2030, 6, 1),
        max_time=datetime(2030, 6, 1, 6, 29, tzinfo=timezone.utc),
        duration_minutes=5.3,
        visibility_regions=["North Africa", "Europe", "Russia"],
        magnitude=0.944,
    ),
    Eclipse(
        eclipse_type=EclipseType.PARTIAL_LUNAR,
        date=date(2030, 6, 15),
        max_time=datetime(2030, 6, 15, 18, 32, tzinfo=timezone.utc),
        visibility_regions=["Europe", "Africa", "Asia", "Australia"],
        magnitude=0.501,
    ),
    Eclipse(
        eclipse_type=EclipseType.TOTAL_SOLAR,
        date=date(2030, 11, 25),
        max_time=datetime(2030, 11, 25, 6, 51, tzinfo=timezone.utc),
        duration_minutes=3.7,
        visibility_regions=["Southern Africa", "Australia"],
        magnitude=1.047,
    ),
    Eclipse(
        eclipse_type=EclipseType.PENUMBRAL_LUNAR,
        date=date(2030, 12, 9),
        max_time=datetime(2030, 12, 9, 22, 27, tzinfo=timezone.utc),
        visibility_regions=["Americas", "Europe", "Africa"],
        magnitude=0.849,
    ),
]


# Type alias for clarity
EclipseInfo = Eclipse


def get_all_eclipses() -> list[Eclipse]:
    """Get list of all eclipses in database."""
    return sorted(ECLIPSES, key=lambda e: e.date)


def get_upcoming_eclipses(
    from_date: date | None = None,
    years: int = 2,
    solar_only: bool = False,
    lunar_only: bool = False,
) -> list[Eclipse]:
    """
    Get upcoming eclipses.

    Args:
        from_date: Start date (defaults to today)
        years: Number of years to look ahead
        solar_only: Only return solar eclipses
        lunar_only: Only return lunar eclipses

    Returns:
        List of upcoming eclipses sorted by date
    """
    if from_date is None:
        from_date = date.today()

    end_date = date(from_date.year + years, from_date.month, from_date.day)

    results = []
    for eclipse in ECLIPSES:
        if eclipse.date < from_date:
            continue
        if eclipse.date > end_date:
            continue
        if solar_only and not eclipse.eclipse_type.is_solar:
            continue
        if lunar_only and not eclipse.eclipse_type.is_lunar:
            continue
        results.append(eclipse)

    return sorted(results, key=lambda e: e.date)


def get_eclipse_info(on_date: date) -> Eclipse | None:
    """
    Get eclipse info for a specific date.

    Args:
        on_date: Date to check

    Returns:
        Eclipse if one occurs on that date, None otherwise
    """
    for eclipse in ECLIPSES:
        if eclipse.date == on_date:
            return eclipse
    return None


def get_next_eclipse(
    from_date: date | None = None,
    solar_only: bool = False,
    lunar_only: bool = False,
) -> Eclipse | None:
    """
    Get the next upcoming eclipse.

    Args:
        from_date: Start date (defaults to today)
        solar_only: Only consider solar eclipses
        lunar_only: Only consider lunar eclipses

    Returns:
        Next eclipse or None if no upcoming eclipses in data
    """
    upcoming = get_upcoming_eclipses(
        from_date=from_date,
        years=10,
        solar_only=solar_only,
        lunar_only=lunar_only,
    )
    return upcoming[0] if upcoming else None


class EclipseClient:
    """Client interface for eclipse data (for consistency with other API clients)."""

    async def get_all_eclipses(self) -> list[Eclipse]:
        """Get all eclipses in database."""
        return get_all_eclipses()

    async def get_upcoming_eclipses(
        self,
        years: int = 2,
        solar_only: bool = False,
        lunar_only: bool = False,
    ) -> list[Eclipse]:
        """Get upcoming eclipses."""
        return get_upcoming_eclipses(
            years=years,
            solar_only=solar_only,
            lunar_only=lunar_only,
        )

    async def get_next_eclipse(
        self,
        solar_only: bool = False,
        lunar_only: bool = False,
    ) -> Eclipse | None:
        """Get the next upcoming eclipse."""
        return get_next_eclipse(
            solar_only=solar_only,
            lunar_only=lunar_only,
        )

    async def close(self) -> None:
        """No-op for API consistency."""
        pass
