"""Moon phase calculations - no API needed, pure math."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum


class MoonPhase(Enum):
    """Moon phase names."""

    NEW_MOON = "New Moon"
    WAXING_CRESCENT = "Waxing Crescent"
    FIRST_QUARTER = "First Quarter"
    WAXING_GIBBOUS = "Waxing Gibbous"
    FULL_MOON = "Full Moon"
    WANING_GIBBOUS = "Waning Gibbous"
    LAST_QUARTER = "Last Quarter"
    WANING_CRESCENT = "Waning Crescent"


@dataclass
class MoonInfo:
    """Moon information for a specific date."""

    date: date
    phase: MoonPhase
    illumination: float  # 0.0 to 1.0
    age_days: float  # Days since new moon (0-29.53)

    @property
    def illumination_percent(self) -> int:
        """Get illumination as percentage."""
        return round(self.illumination * 100)

    @property
    def phase_emoji(self) -> str:
        """Get emoji for current phase."""
        emojis = {
            MoonPhase.NEW_MOON: "🌑",
            MoonPhase.WAXING_CRESCENT: "🌒",
            MoonPhase.FIRST_QUARTER: "🌓",
            MoonPhase.WAXING_GIBBOUS: "🌔",
            MoonPhase.FULL_MOON: "🌕",
            MoonPhase.WANING_GIBBOUS: "🌖",
            MoonPhase.LAST_QUARTER: "🌗",
            MoonPhase.WANING_CRESCENT: "🌘",
        }
        return emojis.get(self.phase, "🌙")

    def __str__(self) -> str:
        return f"{self.phase_emoji} {self.phase.value} ({self.illumination_percent}% illuminated)"


@dataclass
class MoonEvent:
    """A significant moon event (full moon, new moon, etc.)."""

    datetime: datetime
    phase: MoonPhase

    def __str__(self) -> str:
        return f"{self.phase.value}: {self.datetime.strftime('%Y-%m-%d %H:%M UTC')}"


# Synodic month (new moon to new moon) in days
SYNODIC_MONTH = 29.53058867

# Reference new moon (known new moon date for calculations)
# January 6, 2000 at 18:14 UTC was a new moon
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)


def _days_since_reference(dt: datetime) -> float:
    """Get days since reference new moon."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = dt - REFERENCE_NEW_MOON
    return delta.total_seconds() / 86400


def get_moon_age(dt: datetime) -> float:
    """
    Get moon age in days (0 = new moon, ~14.76 = full moon).

    Args:
        dt: DateTime to check

    Returns:
        Age in days (0 to 29.53)
    """
    days = _days_since_reference(dt)
    return days % SYNODIC_MONTH


def get_moon_illumination(dt: datetime) -> float:
    """
    Get approximate moon illumination (0.0 to 1.0).

    This uses a simple cosine approximation.

    Args:
        dt: DateTime to check

    Returns:
        Illumination fraction (0.0 to 1.0)
    """
    age = get_moon_age(dt)
    # Convert age to angle (0 at new moon, π at full moon)
    angle = (age / SYNODIC_MONTH) * 2 * math.pi
    # Illumination follows a (1 - cos) / 2 curve
    return (1 - math.cos(angle)) / 2


def get_moon_phase(dt: datetime) -> MoonPhase:
    """
    Get the moon phase for a given datetime.

    Args:
        dt: DateTime to check

    Returns:
        MoonPhase enum value
    """
    age = get_moon_age(dt)
    # Each phase is ~3.69 days
    phase_length = SYNODIC_MONTH / 8

    if age < phase_length:
        return MoonPhase.NEW_MOON
    elif age < 2 * phase_length:
        return MoonPhase.WAXING_CRESCENT
    elif age < 3 * phase_length:
        return MoonPhase.FIRST_QUARTER
    elif age < 4 * phase_length:
        return MoonPhase.WAXING_GIBBOUS
    elif age < 5 * phase_length:
        return MoonPhase.FULL_MOON
    elif age < 6 * phase_length:
        return MoonPhase.WANING_GIBBOUS
    elif age < 7 * phase_length:
        return MoonPhase.LAST_QUARTER
    else:
        return MoonPhase.WANING_CRESCENT


def get_moon_info(target_date: date | datetime) -> MoonInfo:
    """
    Get moon information for a specific date.

    Args:
        target_date: Date to check

    Returns:
        MoonInfo with phase, illumination, and age
    """
    if isinstance(target_date, date) and not isinstance(target_date, datetime):
        # Use noon UTC for date-only input
        dt = datetime.combine(
            target_date, datetime.min.time().replace(hour=12), tzinfo=timezone.utc
        )
    else:
        dt = target_date
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

    return MoonInfo(
        date=dt.date() if isinstance(dt, datetime) else target_date,
        phase=get_moon_phase(dt),
        illumination=get_moon_illumination(dt),
        age_days=get_moon_age(dt),
    )


def find_next_phase(
    after: datetime,
    target_phase: MoonPhase,
    max_days: int = 60,
) -> datetime | None:
    """
    Find the next occurrence of a specific moon phase.

    Args:
        after: Start searching after this time
        target_phase: Phase to find
        max_days: Maximum days to search

    Returns:
        DateTime of the phase or None if not found
    """
    if after.tzinfo is None:
        after = after.replace(tzinfo=timezone.utc)

    # Binary search within synodic month to find phase transition
    # First, estimate when the phase should occur
    age = get_moon_age(after)

    # Calculate target age based on phase
    phase_ages = {
        MoonPhase.NEW_MOON: 0,
        MoonPhase.WAXING_CRESCENT: SYNODIC_MONTH / 8,
        MoonPhase.FIRST_QUARTER: SYNODIC_MONTH / 4,
        MoonPhase.WAXING_GIBBOUS: 3 * SYNODIC_MONTH / 8,
        MoonPhase.FULL_MOON: SYNODIC_MONTH / 2,
        MoonPhase.WANING_GIBBOUS: 5 * SYNODIC_MONTH / 8,
        MoonPhase.LAST_QUARTER: 3 * SYNODIC_MONTH / 4,
        MoonPhase.WANING_CRESCENT: 7 * SYNODIC_MONTH / 8,
    }

    target_age = phase_ages[target_phase]
    days_until = target_age - age
    if days_until <= 0:
        days_until += SYNODIC_MONTH

    # Estimate datetime
    estimated = after + timedelta(days=days_until)

    # Refine with binary search
    low = estimated - timedelta(hours=12)
    high = estimated + timedelta(hours=12)

    for _ in range(20):  # ~minute precision after 20 iterations
        mid = low + (high - low) / 2
        if get_moon_phase(mid) == target_phase:
            # Found the phase, now find the start
            if get_moon_phase(low) == target_phase:
                return low
            high = mid
        else:
            low = mid

    return low


def get_upcoming_events(
    after: datetime | None = None,
    days: int = 30,
) -> list[MoonEvent]:
    """
    Get upcoming significant moon events (new and full moons).

    Args:
        after: Start time (defaults to now)
        days: Number of days to look ahead

    Returns:
        List of MoonEvent objects
    """
    if after is None:
        after = datetime.now(timezone.utc)
    elif after.tzinfo is None:
        after = after.replace(tzinfo=timezone.utc)

    events = []

    for target_phase in [
        MoonPhase.NEW_MOON,
        MoonPhase.FULL_MOON,
        MoonPhase.FIRST_QUARTER,
        MoonPhase.LAST_QUARTER,
    ]:
        event_time = find_next_phase(after, target_phase)
        if event_time and (event_time - after).days <= days:
            events.append(MoonEvent(datetime=event_time, phase=target_phase))

    # Sort by date
    events.sort(key=lambda e: e.datetime)
    return events


class MoonClient:
    """Client interface for moon data (for consistency with other API clients)."""

    async def get_moon_info(self, target_date: date | None = None) -> MoonInfo:
        """Get moon info for a date."""
        if target_date is None:
            target_date = date.today()
        return get_moon_info(target_date)

    async def get_upcoming_events(self, days: int = 30) -> list[MoonEvent]:
        """Get upcoming moon events."""
        return get_upcoming_events(days=days)

    async def close(self) -> None:
        """No-op for API consistency."""
        pass
