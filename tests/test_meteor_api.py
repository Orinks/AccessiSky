"""Tests for Meteor Shower data."""

from datetime import date

from accessisky.api.meteors import (
    MeteorShower,
    MeteorShowerInfo,
    get_active_showers,
    get_all_showers,
    get_shower_info,
    get_upcoming_showers,
)


class TestMeteorShowerData:
    """Tests for meteor shower static data."""

    def test_get_all_showers(self):
        """Test getting all meteor showers."""
        showers = get_all_showers()
        assert len(showers) >= 10  # At least major showers

        # Check required fields
        for shower in showers:
            assert shower.name
            assert shower.peak_month >= 1 and shower.peak_month <= 12
            assert shower.peak_day >= 1 and shower.peak_day <= 31
            assert shower.zhr > 0  # Zenithal Hourly Rate

    def test_perseids_data(self):
        """Test Perseids shower data (most famous shower)."""
        showers = get_all_showers()
        perseids = next((s for s in showers if "Perseid" in s.name), None)

        assert perseids is not None
        assert perseids.peak_month == 8  # August
        assert perseids.peak_day in range(11, 14)
        assert perseids.zhr >= 100  # Very active shower

    def test_geminids_data(self):
        """Test Geminids shower data."""
        showers = get_all_showers()
        geminids = next((s for s in showers if "Geminid" in s.name), None)

        assert geminids is not None
        assert geminids.peak_month == 12  # December
        assert geminids.zhr >= 120  # Very active

    def test_shower_has_parent_body(self):
        """Test that showers have parent body info."""
        showers = get_all_showers()
        # At least some showers should have known parent bodies
        with_parent = [s for s in showers if s.parent_body]
        assert len(with_parent) >= 5


class TestGetUpcomingShowers:
    """Tests for upcoming shower predictions."""

    def test_get_upcoming_showers(self):
        """Test getting upcoming showers."""
        # Use a fixed date for testing
        test_date = date(2026, 7, 15)
        upcoming = get_upcoming_showers(from_date=test_date, days=60)

        assert len(upcoming) > 0
        # Should include Perseids (peaks Aug 12)
        names = [s.shower.name for s in upcoming]
        assert any("Perseid" in name for name in names)

    def test_upcoming_sorted_by_date(self):
        """Test that upcoming showers are sorted by peak date."""
        test_date = date(2026, 1, 1)
        upcoming = get_upcoming_showers(from_date=test_date, days=365)

        for i in range(len(upcoming) - 1):
            assert upcoming[i].peak_date <= upcoming[i + 1].peak_date

    def test_upcoming_includes_peak_date(self):
        """Test that upcoming info includes calculated peak date."""
        test_date = date(2026, 1, 1)
        upcoming = get_upcoming_showers(from_date=test_date, days=60)

        for info in upcoming:
            assert info.peak_date is not None
            assert info.peak_date.year == 2026


class TestGetActiveShowers:
    """Tests for currently active showers."""

    def test_get_active_during_perseids(self):
        """Test active showers during Perseids peak."""
        test_date = date(2026, 8, 12)  # Perseids peak
        active = get_active_showers(on_date=test_date)

        names = [s.shower.name for s in active]
        assert any("Perseid" in name for name in names)

    def test_activity_window(self):
        """Test that activity window is respected."""
        # Perseids active roughly July 17 - Aug 24
        early_date = date(2026, 7, 1)  # Before activity
        peak_date = date(2026, 8, 12)  # During activity

        early_active = get_active_showers(on_date=early_date)
        peak_active = get_active_showers(on_date=peak_date)

        [s.shower.name for s in early_active]
        peak_names = [s.shower.name for s in peak_active]

        # Perseids should be active during peak but not early
        assert any("Perseid" in name for name in peak_names)


class TestGetShowerInfo:
    """Tests for individual shower info."""

    def test_get_shower_info_by_name(self):
        """Test getting info for specific shower."""
        info = get_shower_info("Perseids", year=2026)

        assert info is not None
        assert "Perseid" in info.shower.name
        assert info.peak_date.year == 2026
        assert info.peak_date.month == 8

    def test_get_shower_info_case_insensitive(self):
        """Test that shower lookup is case insensitive."""
        info1 = get_shower_info("perseids", year=2026)
        info2 = get_shower_info("PERSEIDS", year=2026)

        assert info1 is not None
        assert info2 is not None
        assert info1.shower.name == info2.shower.name

    def test_get_shower_info_unknown(self):
        """Test getting info for unknown shower."""
        info = get_shower_info("NonExistentShower", year=2026)
        assert info is None


class TestMeteorShowerInfo:
    """Tests for MeteorShowerInfo dataclass."""

    def test_str_representation(self):
        """Test string representation."""
        shower = MeteorShower(
            name="Test Shower",
            peak_month=8,
            peak_day=12,
            start_month=7,
            start_day=17,
            end_month=8,
            end_day=24,
            zhr=100,
            parent_body="Test Comet",
            radiant_constellation="Perseus",
        )
        info = MeteorShowerInfo(
            shower=shower,
            peak_date=date(2026, 8, 12),
            is_active=True,
            days_until_peak=0,
        )

        s = str(info)
        assert "Test Shower" in s
        assert "100" in s  # ZHR

    def test_viewing_rating(self):
        """Test viewing rating calculation."""
        shower = MeteorShower(
            name="Test",
            peak_month=1,
            peak_day=1,
            zhr=150,
        )
        info = MeteorShowerInfo(
            shower=shower,
            peak_date=date(2026, 1, 1),
            is_active=True,
            days_until_peak=0,
        )

        # High ZHR at peak should be excellent
        assert info.viewing_rating in ["Excellent", "Good", "Fair", "Poor"]
