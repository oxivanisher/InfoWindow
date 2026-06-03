import os
import tempfile
from pathlib import Path

# Project root is three levels up from this file:
# infowindow/utils/paths.py -> infowindow/utils/ -> infowindow/ -> project root
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
FONTS_DIR: Path = PROJECT_ROOT / "fonts" / "roboto"
ICONS_DIR: Path = PROJECT_ROOT / "icons"


def cache_path(filename: str) -> Path:
    """Return a path inside the systemd CacheDirectory (or system tmp as fallback)."""
    cache_dir = os.environ.get("CACHE_DIRECTORY", tempfile.gettempdir())
    return Path(cache_dir) / filename
