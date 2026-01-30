"""Meteor shower data and predictions - local calculations, no API needed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class MeteorShower:
    """Information about a meteor shower."""

    name: str
    peak_month: int  # 1-12
    peak_day: int  # 1-31
    zhr: int  # Zenithal Hourly Rate at peak
    start_month: int | None = None
    start_day: int | None = None
    end_month: int | None = None
    end_day: int | None = None
    parent_body: str | None = None
    radiant_constellation: str | None = None
    speed_km_s: int | None = None  # Meteor entry speed

    @property
    def activity_days(self) -> int:
        """Approximate number of days the shower is active."""
        if self.start_month and self.end_month:
            # Approximate calculation
            start = date(2000, self.start_month, self.start_day or 1)
            end = date(2000, self.end_month, self.end_day or 28)
            if end < start:
                end = date(2001, self.end_month, self.end_day or 28)
            return (end - start).days
        return 14  # Default 2-week activity window


@dataclass
class MeteorShowerInfo:
    """Information about a meteor shower for a specific time."""

    shower: MeteorShower
    peak_date: date
    is_active: bool
    days_until_peak: int

    @property
    def viewing_rating(self) -> str:
        """Get a qualitative viewing rating."""
        zhr = self.shower.zhr
        days_off = abs(self.days_until_peak)

        # Adjust effective ZHR based on distance from peak
        if days_off == 0:
            effective_zhr = zhr
        elif days_off <= 2:
            effective_zhr = zhr * 0.7
        elif days_off <= 5:
            effective_zhr = zhr * 0.4
        else:
            effective_zhr = zhr * 0.2

        if effective_zhr >= 80:
            return "Excellent"
        elif effective_zhr >= 40:
            return "Good"
        elif effective_zhr >= 15:
            return "Fair"
        else:
            return "Poor"

    def __str__(self) -> str:
        peak_str = self.peak_date.strftime("%b %d")
        status = "Active now" if self.is_active else f"Peaks {peak_str}"
        if self.days_until_peak == 0:
            status = "Peak tonight!"
        elif self.days_until_peak > 0:
            status = f"Peak in {self.days_until_peak} days"
        return f"{self.shower.name}: {status} (ZHR ~{self.shower.zhr}, {self.viewing_rating})"


# Major meteor showers with known dates
# Data from IMO (International Meteor Organization)
METEOR_SHOWERS: list[MeteorShower] = [
    MeteorShower(
        name="Quadrantids",
        peak_month=1,
        peak_day=4,
        start_month=1,
        start_day=1,
        end_month=1,
        end_day=6,
        zhr=120,
        parent_body="Asteroid 2003 EH1",
        radiant_constellation="Boötes",
        speed_km_s=41,
    ),
    MeteorShower(
        name="Lyrids",
        peak_month=4,
        peak_day=22,
        start_month=4,
        start_day=16,
        end_month=4,
        end_day=25,
        zhr=18,
        parent_body="Comet C/1861 G1 Thatcher",
        radiant_constellation="Lyra",
        speed_km_s=49,
    ),
    MeteorShower(
        name="Eta Aquariids",
        peak_month=5,
        peak_day=6,
        start_month=4,
        start_day=19,
        end_month=5,
        end_day=28,
        zhr=50,
        parent_body="Comet 1P/Halley",
        radiant_constellation="Aquarius",
        speed_km_s=66,
    ),
    MeteorShower(
        name="Delta Aquariids",
        peak_month=7,
        peak_day=30,
        start_month=7,
        start_day=12,
        end_month=8,
        end_day=23,
        zhr=25,
        parent_body="Comet 96P/Machholz",
        radiant_constellation="Aquarius",
        speed_km_s=41,
    ),
    MeteorShower(
        name="Perseids",
        peak_month=8,
        peak_day=12,
        start_month=7,
        start_day=17,
        end_month=8,
        end_day=24,
        zhr=100,
        parent_body="Comet 109P/Swift-Tuttle",
        radiant_constellation="Perseus",
        speed_km_s=59,
    ),
    MeteorShower(
        name="Orionids",
        peak_month=10,
        peak_day=21,
        start_month=10,
        start_day=2,
        end_month=11,
        end_day=7,
        zhr=20,
        parent_body="Comet 1P/Halley",
        radiant_constellation="Orion",
        speed_km_s=66,
    ),
    MeteorShower(
        name="Taurids (Southern)",
        peak_month=10,
        peak_day=10,
        start_month=9,
        start_day=10,
        end_month=11,
        end_day=20,
        zhr=5,
        parent_body="Comet 2P/Encke",
        radiant_constellation="Taurus",
        speed_km_s=27,
    ),
    MeteorShower(
        name="Taurids (Northern)",
        peak_month=11,
        peak_day=12,
        start_month=10,
        start_day=20,
        end_month=12,
        end_day=10,
        zhr=5,
        parent_body="Comet 2P/Encke",
        radiant_constellation="Taurus",
        speed_km_s=29,
    ),
    MeteorShower(
        name="Leonids",
        peak_month=11,
        peak_day=17,
        start_month=11,
        start_day=6,
        end_month=11,
        end_day=30,
        zhr=15,
        parent_body="Comet 55P/Tempel-Tuttle",
        radiant_constellation="Leo",
        speed_km_s=71,
    ),
    MeteorShower(
        name="Geminids",
        peak_month=12,
        peak_day=14,
        start_month=12,
        start_day=4,
        end_month=12,
        end_day=20,
        zhr=150,
        parent_body="Asteroid 3200 Phaethon",
        radiant_constellation="Gemini",
        speed_km_s=35,
    ),
    MeteorShower(
        name="Ursids",
        peak_month=12,
        peak_day=22,
        start_month=12,
        start_day=17,
        end_month=12,
        end_day=26,
        zhr=10,
        parent_body="Comet 8P/Tuttle",
        radiant_constellation="Ursa Minor",
        speed_km_s=33,
    ),
]


def get_all_showers() -> list[MeteorShower]:
    """Get list of all known meteor showers."""
    return METEOR_SHOWERS.copy()


def _get_peak_date(shower: MeteorShower, year: int) -> date:
    """Calculate the peak date for a shower in a given year."""
    return date(year, shower.peak_month, shower.peak_day)


def _get_activity_range(shower: MeteorShower, year: int) -> tuple[date, date]:
    """Get the activity date range for a shower in a given year."""
    if shower.start_month and shower.end_month:
        start = date(year, shower.start_month, shower.start_day or 1)
        end = date(year, shower.end_month, shower.end_day or 28)
        # Handle showers that span year boundary
        if shower.end_month < shower.start_month:
            end = date(year + 1, shower.end_month, shower.end_day or 28)
        return (start, end)
    else:
        # Default: 7 days before and after peak
        peak = _get_peak_date(shower, year)
        return (peak - timedelta(days=7), peak + timedelta(days=7))


def _is_shower_active(shower: MeteorShower, on_date: date) -> bool:
    """Check if a shower is active on a given date."""
    year = on_date.year
    start, end = _get_activity_range(shower, year)

    if start <= on_date <= end:
        return True

    # Check previous year (for showers spanning year boundary)
    start_prev, end_prev = _get_activity_range(shower, year - 1)
    return start_prev <= on_date <= end_prev


def get_upcoming_showers(
    from_date: date | None = None,
    days: int = 60,
) -> list[MeteorShowerInfo]:
    """
    Get meteor showers with peaks in the upcoming period.

    Args:
        from_date: Start date (defaults to today)
        days: Number of days to look ahead

    Returns:
        List of MeteorShowerInfo sorted by peak date
    """
    if from_date is None:
        from_date = date.today()

    end_date = from_date + timedelta(days=days)
    results = []

    for shower in METEOR_SHOWERS:
        # Check current year and next year
        for year in [from_date.year, from_date.year + 1]:
            peak = _get_peak_date(shower, year)

            if from_date <= peak <= end_date:
                days_until = (peak - from_date).days
                is_active = _is_shower_active(shower, from_date)

                results.append(
                    MeteorShowerInfo(
                        shower=shower,
                        peak_date=peak,
                        is_active=is_active,
                        days_until_peak=days_until,
                    )
                )

    # Sort by peak date
    results.sort(key=lambda x: x.peak_date)
    return results


def get_active_showers(on_date: date | None = None) -> list[MeteorShowerInfo]:
    """
    Get meteor showers that are currently active.

    Args:
        on_date: Date to check (defaults to today)

    Returns:
        List of active MeteorShowerInfo
    """
    if on_date is None:
        on_date = date.today()

    results = []

    for shower in METEOR_SHOWERS:
        if _is_shower_active(shower, on_date):
            # Find the relevant peak date
            year = on_date.year
            peak = _get_peak_date(shower, year)

            # If peak is before current date and shower spans year boundary
            if peak < on_date:
                next_peak = _get_peak_date(shower, year + 1)
                if (next_peak - on_date).days < (on_date - peak).days:
                    peak = next_peak

            days_until = (peak - on_date).days

            results.append(
                MeteorShowerInfo(
                    shower=shower,
                    peak_date=peak,
                    is_active=True,
                    days_until_peak=days_until,
                )
            )

    return results


def get_shower_info(name: str, year: int | None = None) -> MeteorShowerInfo | None:
    """
    Get information about a specific meteor shower.

    Args:
        name: Shower name (case insensitive, partial match)
        year: Year for peak date calculation (defaults to current year)

    Returns:
        MeteorShowerInfo or None if not found
    """
    if year is None:
        year = date.today().year

    name_lower = name.lower()

    for shower in METEOR_SHOWERS:
        if name_lower in shower.name.lower():
            peak = _get_peak_date(shower, year)
            today = date.today()
            is_active = _is_shower_active(shower, today)
            days_until = (peak - today).days

            return MeteorShowerInfo(
                shower=shower,
                peak_date=peak,
                is_active=is_active,
                days_until_peak=days_until,
            )

    return None


class MeteorClient:
    """Client interface for meteor shower data (for consistency with other API clients)."""

    async def get_all_showers(self) -> list[MeteorShower]:
        """Get all known meteor showers."""
        return get_all_showers()

    async def get_upcoming_showers(self, days: int = 60) -> list[MeteorShowerInfo]:
        """Get upcoming meteor showers."""
        return get_upcoming_showers(days=days)

    async def get_active_showers(self) -> list[MeteorShowerInfo]:
        """Get currently active meteor showers."""
        return get_active_showers()

    async def get_shower_info(self, name: str, year: int | None = None) -> MeteorShowerInfo | None:
        """Get info about a specific shower."""
        return get_shower_info(name, year)

    async def close(self) -> None:
        """No-op for API consistency."""
        pass
