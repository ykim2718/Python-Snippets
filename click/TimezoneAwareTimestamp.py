import click
import pandas as pd
import pytest
from datetime import datetime
import pytz


class TimezoneAwareTimestamp(click.ParamType):
    """
    Click parameter type that validates timezone-aware pandas Timestamp objects.
    """
    name = "timezone_aware_timestamp"

    def __init__(self, default_tz=None):
        """
        Initialize the parameter type.

        Args:
            default_tz (str, optional): Default timezone to apply if timestamp is naive.
                                      If None, naive timestamps will be rejected.
        """
        self.default_tz = default_tz

    def convert(self, value, param, ctx):
        """
        Convert and validate the input value to a timezone-aware pandas Timestamp.

        Args:
            value: Input value to convert
            param: Click parameter object
            ctx: Click context object

        Returns:
            pd.Timestamp: Timezone-aware pandas Timestamp
        """
        if value is None:
            return value

        # If it's already a pd.Timestamp
        if isinstance(value, pd.Timestamp):
            if value.tz is None:
                if self.default_tz:
                    # Localize to default timezone
                    return value.tz_localize(self.default_tz)
                else:
                    self.fail(f"Timestamp must be timezone-aware: {value}", param, ctx)
            return value

        # Try to parse string
        if isinstance(value, str):
            try:
                # First try to parse with timezone info
                ts = pd.Timestamp(value)
                if ts.tz is None:
                    if self.default_tz:
                        return ts.tz_localize(self.default_tz)
                    else:
                        self.fail(f"Parsed timestamp must include timezone info: {value}", param, ctx)
                return ts
            except Exception as e:
                self.fail(f"Could not parse timestamp: {value}. Error: {e}", param, ctx)

        # Try to convert datetime objects
        if isinstance(value, datetime):
            ts = pd.Timestamp(value)
            if ts.tz is None:
                if self.default_tz:
                    return ts.tz_localize(self.default_tz)
                else:
                    self.fail(f"Datetime must be timezone-aware: {value}", param, ctx)
            return ts

        self.fail(f"Expected timezone-aware timestamp, got {type(value).__name__}: {value}", param, ctx)


# Example CLI commands for demonstration
@click.command()
@click.option('--timestamp', type=TimezoneAwareTimestamp(),
              help='Timezone-aware timestamp (e.g., "2023-01-01 12:00:00+09:00")')
def process_timestamp(timestamp):
    """Process a timezone-aware timestamp."""
    if timestamp:
        click.echo(f"Received timestamp: {timestamp}")
        click.echo(f"Timezone: {timestamp.tz}")
        click.echo(f"UTC timestamp: {timestamp.tz_convert('UTC')}")
    else:
        click.echo("No timestamp provided")


@click.command()
@click.option('--timestamp', type=TimezoneAwareTimestamp(default_tz='UTC'),
              help='Timestamp (will be localized to UTC if naive)')
def process_timestamp_with_default(timestamp):
    """Process a timestamp with default timezone."""
    if timestamp:
        click.echo(f"Received timestamp: {timestamp}")
        click.echo(f"Timezone: {timestamp.tz}")
    else:
        click.echo("No timestamp provided")


# Test cases
def test_timezone_aware_timestamp():
    """Test the TimezoneAwareTimestamp parameter type."""

    # Test with no default timezone
    param_type = TimezoneAwareTimestamp()

    # Test valid timezone-aware timestamp string
    result = param_type.convert("2023-01-01 12:00:00+09:00", None, None)
    assert isinstance(result, pd.Timestamp)
    assert result.tz is not None
    assert str(result.tz) == "+09:00"

    # Test valid timezone-aware pandas Timestamp
    ts_aware = pd.Timestamp("2023-01-01 12:00:00", tz='Asia/Seoul')
    result = param_type.convert(ts_aware, None, None)
    assert isinstance(result, pd.Timestamp)
    assert result.tz is not None
    assert result.tzinfo.zone == 'Asia/Seoul'

    # Test with default timezone
    param_type_with_default = TimezoneAwareTimestamp(default_tz='UTC')

    # Test naive timestamp with default timezone
    result = param_type_with_default.convert("2023-01-01 12:00:00", None, None)
    assert isinstance(result, pd.Timestamp)
    assert result.tz is not None
    assert str(result.tz) == 'UTC'

    # Test naive pandas Timestamp with default timezone
    ts_naive = pd.Timestamp("2023-01-01 12:00:00")
    result = param_type_with_default.convert(ts_naive, None, None)
    assert isinstance(result, pd.Timestamp)
    assert result.tz is not None
    assert str(result.tz) == 'UTC'

    # Test None value
    result = param_type.convert(None, None, None)
    assert result is None


def test_timezone_aware_timestamp_failures():
    """Test failure cases for TimezoneAwareTimestamp."""

    param_type = TimezoneAwareTimestamp()

    # Test naive timestamp without default timezone (should fail)
    try:
        param_type.convert("2023-01-01 12:00:00", None, None)
        assert False, "Should have failed for naive timestamp"
    except click.BadParameter:
        pass

    # Test naive pandas Timestamp without default timezone (should fail)
    try:
        ts_naive = pd.Timestamp("2023-01-01 12:00:00")
        param_type.convert(ts_naive, None, None)
        assert False, "Should have failed for naive pandas Timestamp"
    except click.BadParameter:
        pass

    # Test invalid string (should fail)
    try:
        param_type.convert("invalid-timestamp", None, None)
        assert False, "Should have failed for invalid timestamp string"
    except click.BadParameter:
        pass

    # Test invalid type (should fail)
    try:
        param_type.convert(12345, None, None)
        assert False, "Should have failed for invalid type"
    except click.BadParameter:
        pass


def test_datetime_conversion():
    """Test datetime object conversion."""

    param_type = TimezoneAwareTimestamp(default_tz='Asia/Tokyo')

    # Test timezone-aware datetime
    dt_aware = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
    result = param_type.convert(dt_aware, None, None)
    assert isinstance(result, pd.Timestamp)
    assert result.tz is not None

    # Test naive datetime with default timezone
    dt_naive = datetime(2023, 1, 1, 12, 0, 0)
    result = param_type.convert(dt_naive, None, None)
    assert isinstance(result, pd.Timestamp)
    assert result.tz is not None
    assert result.tzinfo.zone == 'Asia/Tokyo'


if __name__ == "__main__":
    # Run tests
    print("Running tests...")
    test_timezone_aware_timestamp()
    test_timezone_aware_timestamp_failures()
    test_datetime_conversion()
    print("All tests passed!")

    # Example usage
    print("\nExample usage:")
    print("python script.py process-timestamp --timestamp '2023-01-01 12:00:00+09:00'")
    print("python script.py process-timestamp-with-default --timestamp '2023-01-01 12:00:00'")
