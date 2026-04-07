"""
SportZap — FastAPI Application

Endpoints:
  GET /api/events         → list sport events (filterable by date, sport, channel)
  GET /api/events/{id}    → single event detail
  GET /api/channels       → list all sport-relevant channels
  GET /api/sports         → list available sport types
  GET /api/health         → service health + data freshness
  POST /api/refresh       → force XMLTV re-download + parse

Query parameters:
  ?date=2026-03-29        → filter by date (default: today)
  ?sport=football         → filter by sport type
  ?channel=canal-plus     → filter by channel slug
  ?free_only=true         → only free TNT channels

Designed to be consumed by the React Native / Expo mobile app.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .fetcher import XMLTVFetcher
from .models import DaySchedule, SportEvent, SportType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("sportzap")

# ── Global fetcher instance ──
fetcher = XMLTVFetcher(source="full")


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup: load XMLTV data. On shutdown: cleanup."""
    logger.info("SportZap starting up...")

    # Try to load from sample data for development
    sample = Path(__file__).parent.parent / "data" / "sample_xmltv.xml"
    if sample.exists():
        logger.info(f"Loading sample XMLTV: {sample}")
        fetcher.parse(source_override=sample)
    else:
        # Production: download from xmltvfr.fr
        await fetcher.refresh()

    logger.info(f"Ready — {fetcher.stats['cached_events']} sport events loaded")
    yield
    logger.info("SportZap shutting down.")


# ── App ──
app = FastAPI(
    title="SportZap API",
    description="Programme TV Sport — France",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.get("/api/events", response_model=DaySchedule)
async def get_events(
    date: Optional[str] = Query(
        None,
        description="ISO date YYYY-MM-DD (default: today)",
        examples=["2026-03-29"],
    ),
    sport: Optional[str] = Query(None, description="Sport type filter"),
    channel: Optional[str] = Query(None, description="Channel slug filter"),
    free_only: bool = Query(False, description="Only free TNT channels"),
):
    """
    Get sport events for a given day.

    Returns events sorted: live first, then upcoming by time, then finished.
    """
    # Default to today
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    events = fetcher.get_events(date=date, sport=sport, channel_slug=channel)

    if free_only:
        events = [e for e in events if e.channel.is_free]

    live_count = sum(1 for e in events if e.status == "live")

    return DaySchedule(
        date=date,
        event_count=len(events),
        live_count=live_count,
        events=events,
    )


@app.get("/api/events/{event_id}", response_model=SportEvent)
async def get_event(event_id: str):
    """Get a single sport event by ID."""
    for event in fetcher._events:
        if event.id == event_id:
            return event
    raise HTTPException(status_code=404, detail="Event not found")


@app.get("/api/channels")
async def get_channels():
    """List all channels with sport programming."""
    from .sport_extractor import build_channel

    raw_channels = fetcher.get_channels()
    channels = [build_channel(ch) for ch in raw_channels]

    # Only return channels that have at least one sport event
    active_slugs = {e.channel.slug for e in fetcher._events}
    sport_channels = [ch for ch in channels if ch.slug in active_slugs]

    return {
        "channels": [ch.model_dump() for ch in sport_channels],
        "total": len(sport_channels),
    }


@app.get("/api/sports")
async def get_sports():
    """List all sport types with event counts."""
    counts: dict[str, int] = {}
    for event in fetcher._events:
        sport_val = event.sport.value
        counts[sport_val] = counts.get(sport_val, 0) + 1

    return {
        "sports": [
            {
                "id": sport.value,
                "label": sport.value.replace("_", " ").title(),
                "event_count": counts.get(sport.value, 0),
            }
            for sport in SportType
            if counts.get(sport.value, 0) > 0
        ]
    }


@app.get("/api/health")
async def health():
    """Service health check with data freshness info."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "data": fetcher.stats,
    }


@app.post("/api/refresh")
async def refresh():
    """Force re-download and re-parse of XMLTV data."""
    events = await fetcher.refresh()
    return {
        "status": "refreshed",
        "event_count": len(events),
        "data": fetcher.stats,
    }
