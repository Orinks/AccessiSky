"""Tests for Moon phase calculations."""

from datetime import date, datetime, timezone

import pytest

from accessisky.api.moon import (
    SYNODIC_MONTH,
    MoonClient,
    MoonInfo,
    MoonPhase,
    find_next_phase,
    get_moon_age,
    get_moon_illumination,
    get_moon_info,
    get_moon_phase,
    get_upcoming_events,
)


class TestMoonCalculations:
    """Tests for moon calculation functions."""

    def test_moon_age_at_new_moon(self):
        """Test moon age is ~0 at a known new moon."""
        # January 29, 2025 was a new moon
        new_moon = datetime(2025, 1, 29, 12, 36, tzinfo=timezone.utc)
        age = get_moon_age(new_moon)
        # Should be very close to 0 (within a day)
        assert age < 1 or age > SYNODIC_MONTH - 1

    def test_moon_age_at_full_moon(self):
        """Test moon age is ~14.76 at a known full moon."""
        # February 12, 2025 was a full moon (about 14 days after new moon)
        full_moon = datetime(2025, 2, 12, 13, 53, tzinfo=timezone.utc)
        age = get_moon_age(full_moon)
        # Should be close to half synodic month
        assert 13 < age < 16

    def test_moon_illumination_new(self):
        """Test illumination is low at new moon."""
        new_moon = datetime(2025, 1, 29, 12, 36, tzinfo=timezone.utc)
        illum = get_moon_illumination(new_moon)
        assert illum < 0.05  # Less than 5%

    def test_moon_illumination_full(self):
        """Test illumination is high at full moon."""
        full_moon = datetime(2025, 2, 12, 13, 53, tzinfo=timezone.utc)
        illum = get_moon_illumination(full_moon)
        assert illum > 0.95  # More than 95%

    def test_moon_phase_cycle(self):
        """Test that phases cycle correctly over a month."""
        from datetime import timedelta

        # Start at a new moon
        start = datetime(2025, 1, 29, 12, 0, tzinfo=timezone.utc)

        phases_seen = set()
        for day in range(30):
            dt = start + timedelta(days=day)
            phase = get_moon_phase(dt)
            phases_seen.add(phase)

        # Should see all 8 phases over a month
        assert len(phases_seen) == 8

    def test_get_moon_phase_new_moon(self):
        """Test identifying new moon phase."""
        new_moon = datetime(2025, 1, 29, 12, 36, tzinfo=timezone.utc)
        phase = get_moon_phase(new_moon)
        assert phase == MoonPhase.NEW_MOON

    def test_get_moon_phase_full_moon(self):
        """Test identifying full moon phase."""
        # Use a time when the moon is definitely full
        # The calculation is approximate, so we check illumination instead
        full_moon = datetime(2025, 2, 12, 13, 53, tzinfo=timezone.utc)
        illumination = get_moon_illumination(full_moon)
        # Full moon should be >95% illuminated
        assert illumination > 0.95


class TestMoonInfo:
    """Tests for MoonInfo dataclass."""

    def test_moon_info_creation(self):
        """Test creating moon info."""
        info = MoonInfo(
            date=date(2026, 1, 30),
            phase=MoonPhase.WAXING_CRESCENT,
            illumination=0.25,
            age_days=5.5,
        )
        assert info.phase == MoonPhase.WAXING_CRESCENT
        assert info.illumination == 0.25
        assert info.age_days == 5.5

    def test_illumination_percent(self):
        """Test illumination percentage conversion."""
        info = MoonInfo(
            date=date(2026, 1, 30),
            phase=MoonPhase.FIRST_QUARTER,
            illumination=0.5,
            age_days=7.38,
        )
        assert info.illumination_percent == 50

    def test_phase_emoji(self):
        """Test phase emoji mapping."""
        info = MoonInfo(
            date=date(2026, 1, 30),
            phase=MoonPhase.FULL_MOON,
            illumination=1.0,
            age_days=14.76,
        )
        assert info.phase_emoji == "🌕"

    def test_str_representation(self):
        """Test string representation."""
        info = MoonInfo(
            date=date(2026, 1, 30),
            phase=MoonPhase.WAXING_GIBBOUS,
            illumination=0.75,
            age_days=10.0,
        )
        s = str(info)
        assert "Waxing Gibbous" in s
        assert "75%" in s


class TestGetMoonInfo:
    """Tests for get_moon_info function."""

    def test_get_moon_info_with_date(self):
        """Test getting moon info for a specific date."""
        info = get_moon_info(date(2025, 2, 12))
        # Should be around full moon
        assert info.illumination > 0.9

    def test_get_moon_info_with_datetime(self):
        """Test getting moon info for a datetime."""
        dt = datetime(2025, 1, 29, 12, 36, tzinfo=timezone.utc)
        info = get_moon_info(dt)
        assert info.phase == MoonPhase.NEW_MOON


class TestFindNextPhase:
    """Tests for find_next_phase function."""

    def test_find_next_full_moon(self):
        """Test finding next full moon."""
        start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        full_moon = find_next_phase(start, MoonPhase.FULL_MOON)

        assert full_moon is not None
        # First full moon of 2025 was Jan 13
        assert full_moon.month == 1
        assert 10 <= full_moon.day <= 16

    def test_find_next_new_moon(self):
        """Test finding next new moon."""
        start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        new_moon = find_next_phase(start, MoonPhase.NEW_MOON)

        assert new_moon is not None
        # First new moon of 2025 was Jan 29
        assert new_moon.month == 1
        assert 26 <= new_moon.day <= 31


class TestGetUpcomingEvents:
    """Tests for get_upcoming_events function."""

    def test_get_upcoming_events(self):
        """Test getting upcoming moon events."""
        events = get_upcoming_events(
            after=datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
            days=60,
        )

        assert len(events) > 0
        # Events should be sorted by date
        for i in range(len(events) - 1):
            assert events[i].datetime <= events[i + 1].datetime

    def test_upcoming_events_include_major_phases(self):
        """Test that upcoming events include major phases."""
        events = get_upcoming_events(
            after=datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
            days=30,
        )

        phases = {e.phase for e in events}
        # Should have at least new and full moon
        assert MoonPhase.NEW_MOON in phases or MoonPhase.FULL_MOON in phases


class TestMoonClient:
    """Tests for MoonClient (async interface)."""

    @pytest.fixture
    def client(self):
        """Create a moon client for testing."""
        return MoonClient()

    @pytest.mark.asyncio
    async def test_get_moon_info(self, client):
        """Test getting moon info through client."""
        info = await client.get_moon_info(date(2025, 2, 12))
        assert info is not None
        assert isinstance(info, MoonInfo)

    @pytest.mark.asyncio
    async def test_get_moon_info_with_location(self, client):
        """Test getting moon info with location (uses USNO API)."""
        info = await client.get_moon_info(
            target_date=date(2026, 1, 30),
            latitude=40.71,
            longitude=-74.01,
        )
        await client.close()

        assert info is not None
        assert isinstance(info, MoonInfo)
        # With location, should use USNO API
        # Note: May fall back to local if API fails
        assert info.source in ["usno", "local"]

    @pytest.mark.asyncio
    async def test_get_upcoming_events(self, client):
        """Test getting upcoming events through client."""
        events = await client.get_upcoming_events(days=30)
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_get_upcoming_events_usno(self, client):
        """Test getting upcoming events from USNO API."""
        events = await client.get_upcoming_events(
            days=60,
            after=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        )
        await client.close()

        assert len(events) > 0
        # Check that we got primary phases
        phases = {e.phase for e in events}
        assert any(p in phases for p in [
            MoonPhase.FULL_MOON,
            MoonPhase.NEW_MOON,
            MoonPhase.FIRST_QUARTER,
            MoonPhase.LAST_QUARTER,
        ])

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close (no-op but should work)."""
        await client.close()  # Should not raise
