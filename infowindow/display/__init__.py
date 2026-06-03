import logging

log = logging.getLogger(__name__)


def get_display():
    """Return a real EPD device, or a MockEPD when hardware is unavailable."""
    try:
        from infowindow.display.epd import RealEPD
        return RealEPD()
    except Exception as exc:
        log.info("E-ink driver unavailable (%s), using mock display.", exc)
        from infowindow.display.mock import MockEPD
        return MockEPD()
