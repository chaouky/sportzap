"""
SportZap — XMLTV Fetcher

Downloads XMLTV data from xmltvfr.fr on a schedule,
caches it locally, and provides the parsed output.

In production, this runs as a background task (cron or APScheduler)
every 4-6 hours to stay fresh.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from .models import SportEvent
from .xmltv_parser import parse_xmltv
from .sport_extractor import extract_sport_events

logger = logging.getLogger(__name__)

# ── XMLTV Sources ──
# xmltvfr.fr provides several feeds:
#   - TNT only (~27 channels, small file)
#   - Full France (~402 channels, ~8MB compressed)
XMLTV_SOURCES = {
    "tnt": {
        "url": "https://xmltvfr.fr/xmltv/xmltv.zip",
        "description": "TNT channels only",
    },
    "full": {
        "url": "https://xmltvfr.fr/xmltv/xmltv.zip",
        "description": "All 402+ French channels",
    },
}

# Default cache directory
CACHE_DIR = Path("/tmp/sportzap_cache")


class XMLTVFetcher:
    """
    Manages XMLTV data lifecycle:
    - Download from xmltvfr.fr
    - Cache locally
    - Parse and extract sport events
    - Refresh on schedule
    """

    def __init__(
        self,
        source: str = "full",
        cache_dir: Path = CACHE_DIR,
        max_age_hours: int = 6,
    ):
        self.source_key = source
        self.source = XMLTV_SOURCES[source]
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._events: list[SportEvent] = []
        self._channels: dict = {}
        self._last_fetch: Optional[datetime] = None
        self._last_parse: Optional[datetime] = None

    @property
    def cache_path(self) -> Path:
        return self.cache_dir / f"xmltv_{self.source_key}.zip"

    @property
    def is_stale(self) -> bool:
        """Check if cached data needs refresh."""
        if not self.cache_path.exists():
            return True
        if not self._last_fetch:
            return True
        age_hours = (datetime.now(timezone.utc) - self._last_fetch).total_seconds() / 3600
        return age_hours >= self.max_age_hours

    async def download(self) -> bool:
        """Download fresh XMLTV data from source URL."""
        url = self.source["url"]
        logger.info(f"Downloading XMLTV from {url}...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                self.cache_path.write_bytes(resp.content)
                self._last_fetch = datetime.now(timezone.utc)

                size_mb = len(resp.content) / (1024 * 1024)
                logger.info(f"  → Downloaded {size_mb:.1f} MB to {self.cache_path}")
                return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to download XMLTV: {e}")
            return False

    def parse(self, source_override: Optional[Path] = None) -> list[SportEvent]:
        """Parse cached (or overridden) XMLTV file into sport events."""
        source = source_override or self.cache_path

        if not source.exists():
            logger.warning(f"XMLTV file not found: {source}")
            return []

        t0 = time.monotonic()

        channels, programmes = parse_xmltv(source)
        self._channels = channels

        events = extract_sport_events(programmes, channels)
        self._events = events
        self._last_parse = datetime.now(timezone.utc)

        elapsed = time.monotonic() - t0
        logger.info(f"Parsed {len(events)} sport events in {elapsed:.2f}s")

        return events

    async def refresh(self) -> list[SportEvent]:
        """Download (if stale) + parse. Main entry point."""
        if self.is_stale:
            success = await self.download()
            if not success and not self.cache_path.exists():
                logger.error("No XMLTV data available")
                return []

        return self.parse()

    def get_events(
        self,
        date: Optional[str] = None,
        sport: Optional[str] = None,
        channel_slug: Optional[str] = None,
    ) -> list[SportEvent]:
        """
        Query cached events with optional filters.

        Args:
            date: ISO date string "YYYY-MM-DD"
            sport: SportType value
            channel_slug: normalized channel slug
        """
        filtered = self._events

        if date:
            filtered = [
                e for e in filtered
                if e.start.strftime("%Y-%m-%d") == date
            ]

        if sport:
            filtered = [
                e for e in filtered
                if e.sport.value == sport
            ]

        if channel_slug:
            filtered = [
                e for e in filtered
                if e.channel.slug == channel_slug
            ]

        return filtered

    def get_channels(self) -> list[dict]:
        """Return parsed channel list."""
        return list(self._channels.values())

    @property
    def stats(self) -> dict:
        return {
            "source": self.source_key,
            "cached_events": len(self._events),
            "cached_channels": len(self._channels),
            "last_fetch": self._last_fetch.isoformat() if self._last_fetch else None,
            "last_parse": self._last_parse.isoformat() if self._last_parse else None,
            "is_stale": self.is_stale,
        }
