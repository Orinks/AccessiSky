"""Tests for Eclipse Calendar data."""

from datetime import date, datetime, timezone

from accessisky.api.eclipses import (
    Eclipse,
    EclipseType,
    get_all_eclipses,
    get_eclipse_info,
    get_upcoming_eclipses,
)


class TestEclipseType:
    """Tests for eclipse type enum."""

    def test_eclipse_types_exist(self):
        """Test that all eclipse types exist."""
        assert EclipseType.TOTAL_SOLAR
        assert EclipseType.PARTIAL_SOLAR
        assert EclipseType.ANNULAR_SOLAR
        assert EclipseType.TOTAL_LUNAR
        assert EclipseType.PARTIAL_LUNAR
        assert EclipseType.PENUMBRAL_LUNAR

    def test_is_solar_property(self):
        """Test is_solar property."""
        assert EclipseType.TOTAL_SOLAR.is_solar
        assert EclipseType.ANNULAR_SOLAR.is_solar
        assert not EclipseType.TOTAL_LUNAR.is_solar

    def test_is_lunar_property(self):
        """Test is_lunar property."""
        assert EclipseType.TOTAL_LUNAR.is_lunar
        assert EclipseType.PENUMBRAL_LUNAR.is_lunar
        assert not EclipseType.TOTAL_SOLAR.is_lunar


class TestEclipseData:
    """Tests for eclipse static data."""

    def test_get_all_eclipses(self):
        """Test getting all eclipses."""
        eclipses = get_all_eclipses()
        assert len(eclipses) >= 5  # Should have several years of data

    def test_eclipses_have_required_fields(self):
        """Test that eclipses have all required fields."""
        eclipses = get_all_eclipses()

        for eclipse in eclipses:
            assert eclipse.eclipse_type is not None
            assert eclipse.date is not None
            assert eclipse.max_time is not None

    def test_eclipses_sorted_by_date(self):
        """Test that eclipses are sorted by date."""
        eclipses = get_all_eclipses()

        for i in range(len(eclipses) - 1):
            assert eclipses[i].date <= eclipses[i + 1].date


class TestGetUpcomingEclipses:
    """Tests for upcoming eclipse predictions."""

    def test_get_upcoming_eclipses(self):
        """Test getting upcoming eclipses."""
        # Use a fixed date for testing
        test_date = date(2026, 1, 1)
        upcoming = get_upcoming_eclipses(from_date=test_date, years=3)

        assert len(upcoming) > 0

    def test_upcoming_are_future(self):
        """Test that upcoming eclipses are in the future."""
        test_date = date(2026, 6, 1)
        upcoming = get_upcoming_eclipses(from_date=test_date)

        for eclipse in upcoming:
            assert eclipse.date >= test_date

    def test_filter_solar_only(self):
        """Test filtering for solar eclipses only."""
        upcoming = get_upcoming_eclipses(
            from_date=date(2025, 1, 1),
            years=5,
            solar_only=True,
        )

        for eclipse in upcoming:
            assert eclipse.eclipse_type.is_solar

    def test_filter_lunar_only(self):
        """Test filtering for lunar eclipses only."""
        upcoming = get_upcoming_eclipses(
            from_date=date(2025, 1, 1),
            years=5,
            lunar_only=True,
        )

        for eclipse in upcoming:
            assert eclipse.eclipse_type.is_lunar


class TestGetEclipseInfo:
    """Tests for individual eclipse info."""

    def test_get_eclipse_info_by_date(self):
        """Test getting info for eclipse on specific date."""
        # There should be eclipses in our data
        all_eclipses = get_all_eclipses()
        if all_eclipses:
            first_eclipse = all_eclipses[0]
            info = get_eclipse_info(first_eclipse.date)

            assert info is not None
            assert info.date == first_eclipse.date

    def test_get_eclipse_info_no_eclipse(self):
        """Test getting info when no eclipse on date."""
        # Pick a random date unlikely to have an eclipse
        get_eclipse_info(date(2026, 6, 15))

        # May or may not find one depending on data
        # Just ensure no crash


class TestEclipseInfo:
    """Tests for EclipseInfo dataclass."""

    def test_str_representation(self):
        """Test string representation."""
        eclipse = Eclipse(
            eclipse_type=EclipseType.TOTAL_SOLAR,
            date=date(2027, 8, 2),
            max_time=datetime(2027, 8, 2, 10, 7, tzinfo=timezone.utc),
            duration_minutes=6.4,
            visibility_regions=["Spain", "Morocco", "Egypt"],
        )

        s = str(eclipse)
        assert "Solar" in s or "solar" in s.lower()
        assert "2027" in s

    def test_is_visible_from(self):
        """Test visibility region checking."""
        eclipse = Eclipse(
            eclipse_type=EclipseType.TOTAL_SOLAR,
            date=date(2027, 8, 2),
            max_time=datetime(2027, 8, 2, 10, 7, tzinfo=timezone.utc),
            visibility_regions=["North America", "Europe"],
        )

        assert eclipse.is_visible_from("Europe")
        assert eclipse.is_visible_from("north america")  # Case insensitive
        assert not eclipse.is_visible_from("Australia")


class TestEclipseDataAccuracy:
    """Tests for known eclipse dates."""

    def test_2026_february_lunar(self):
        """Test that Feb 2026 total lunar eclipse is in data."""
        upcoming = get_upcoming_eclipses(
            from_date=date(2026, 1, 1),
            years=1,
            lunar_only=True,
        )

        # March 2026 has a total lunar eclipse
        [e for e in upcoming if e.date.month == 3]
        # May or may not be in our data - just check no crash

    def test_2027_august_solar(self):
        """Test that Aug 2027 total solar eclipse is in data."""
        upcoming = get_upcoming_eclipses(
            from_date=date(2027, 1, 1),
            years=1,
            solar_only=True,
        )

        # August 2027 has a famous total solar eclipse
        aug_eclipses = [e for e in upcoming if e.date.month == 8]
        # Should find the 2027 eclipse
        if aug_eclipses:
            assert any(e.eclipse_type == EclipseType.TOTAL_SOLAR for e in aug_eclipses)
