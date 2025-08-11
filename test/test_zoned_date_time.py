'''tests related to the zoned datetime conversion'''
import pytest
from rune.runtime.utils import rune_zoned_date_time as rdt


def test_naive():
    '''no tz'''
    assert rdt("2025-01-02 03:04:05").tzinfo is None


def test_offset_only():
    '''standard offset, no tz'''
    d = rdt("2025-01-02 03:04:05 +02:00")
    assert str(d.utcoffset()) == "2:00:00"


def test_zone_only():
    '''tz  present'''
    d = rdt("2025-01-02 03:04:05 Europe/Paris")
    assert d.tzinfo.key == "Europe/Paris"  # type: ignore


def test_offset_and_zone_match():
    '''tz and offset present'''
    rdt("2025-01-02 03:04:05 +01:00 Europe/Paris")  # should not raise


def test_offset_and_zone_mismatch():
    '''tz and offset present but do not match'''
    with pytest.raises(ValueError):
        rdt("2025-01-02 03:04:05 +03:00 Europe/Paris")

# EOF
