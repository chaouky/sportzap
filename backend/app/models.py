"""
SportZap — Data models
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SportType(str, Enum):
    FOOTBALL = "football"
    RUGBY = "rugby"
    TENNIS = "tennis"
    BASKET = "basket"
    F1 = "f1"
    CYCLISME = "cyclisme"
    MMA = "mma"
    HANDBALL = "handball"
    NATATION = "natation"
    ATHLETISME = "athletisme"
    SKI = "ski"
    GOLF = "golf"
    VOILE = "voile"
    EQUITATION = "equitation"
    MOTOGP = "motogp"
    BOXE = "boxe"
    VOLLEYBALL = "volleyball"
    OTHER = "other"


class EntityType(str, Enum):
    CLUB = "club"
    COUNTRY = "country"
    PLAYER = "player"
    EVENT = "event"


class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    LIVE = "live"
    FINISHED = "finished"


# ── Channel ──

class Channel(BaseModel):
    id: str = Field(..., description="XMLTV channel ID")
    name: str = Field(..., description="Display name, e.g. 'Canal+'")
    icon_url: Optional[str] = None
    slug: str = Field(..., description="Normalized slug, e.g. 'canal-plus'")
    is_free: bool = Field(False, description="Available on free TNT")


# ── Entity (team / player / country) ──

class Entity(BaseModel):
    name: str
    type: EntityType
    short: Optional[str] = None
    country_code: Optional[str] = None
    logo_url: Optional[str] = None
    photo_url: Optional[str] = None


# ── Sport Event ──

class SportEvent(BaseModel):
    id: str = Field(..., description="Unique event hash")
    sport: SportType
    competition: Optional[str] = Field(None, description="e.g. 'Ligue 1 · J29'")
    title: str = Field(..., description="Raw XMLTV title")
    subtitle: Optional[str] = None
    description: Optional[str] = None

    team1: Optional[Entity] = None
    team2: Optional[Entity] = None

    channel: Channel
    start: datetime
    end: datetime
    status: EventStatus = EventStatus.UPCOMING

    # Live enrichment (from API-Sports later)
    score1: Optional[int] = None
    score2: Optional[int] = None
    minute: Optional[str] = None
    result: Optional[str] = None


# ── API Responses ──

class DaySchedule(BaseModel):
    date: str = Field(..., description="ISO date, e.g. '2026-03-29'")
    event_count: int
    live_count: int
    events: list[SportEvent]


class ChannelListResponse(BaseModel):
    channels: list[Channel]
    total: int
