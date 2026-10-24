"""
SportZap — Affinage du programme : coup d'envoi réel + suppression des rediffusions.

Le XMLTV liste des *diffusions*, pas des matchs : une même rencontre y apparaît
dix fois (direct, puis rediffusions la nuit, le lendemain, la semaine suivante),
et l'heure de chaque ligne est celle où la chaîne commence son antenne
(avant-match compris), pas le coup d'envoi.

`refine_events` :
  1. retire les diffusions qui ne sont pas un match complet (avant-matchs,
     résumés : durée trop courte) et celles que le texte désigne comme
     rediffusion (« Revivez la rencontre… », « en différé »…) ;
  2. recale chaque match sur le calendrier officiel (ESPN) quand il est connu :
     une diffusion hors de la fenêtre [coup d'envoi − 150 min, + 20 min] est une
     rediffusion ; sinon l'heure officielle devient `kickoff` ;
  3. pour le reste, applique des règles prudentes :
       - football/rugby/… européen « en direct » à 00h-11h = rediffusion ;
       - un même duo d'équipes diffusé plusieurs fois : seule la 1re vague
         (± 75 min) est le direct, les suivantes sont des rediffusions ;
  4. estime le coup d'envoi des sports collectifs sans calendrier :
     début de diffusion arrondi au quart d'heure suivant s'il est à ≤ 10 min.
"""
from __future__ import annotations

import hashlib
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

from .fixtures import Fixture, fixture_matches, fold
from .models import Channel, Entity, EntityType, EventStatus, SportEvent, SportType

logger = logging.getLogger(__name__)

PARIS = ZoneInfo("Europe/Paris")

TEAM_SPORTS = {"football", "rugby", "handball", "basket", "volleyball"}
# Durée minimale d'une vraie diffusion de match (minutes) — en dessous :
# avant-match, flash, résumé.
MIN_DURATION = {"football": 75, "rugby": 75, "handball": 55, "basket": 60, "volleyball": 55}

# Fenêtre de diffusion « en direct » autour du coup d'envoi officiel
BEFORE_KICKOFF = timedelta(minutes=150)   # l'antenne peut s'ouvrir très tôt
AFTER_KICKOFF = timedelta(minutes=20)     # tolérance de retard
LIVE_WAVE = timedelta(minutes=75)         # écart max entre chaînes d'un même direct

# Textes qui désignent sans ambiguïté une rediffusion. (« Retransmission d'un
# match… » est la formule standard de toutes les diffusions, directs compris :
# on ne s'en sert pas.)
_REPLAY_TEXT = re.compile(
    r"(?i)\b(revivez|rediffusion|redif|en diff[eé]r[eé]|diff[eé]r[eé]|replay|"
    r"match en int[eé]gralit[eé]|int[eé]grale du match|rerun)\b|\(r\)"
    # segments de match diffusés seuls (« 1ère période du match de la Journée 8… »)
    r"|\b(1[èe]re|2[eè]?me?|premi[èe]re|seconde)\s+(p[ée]riode|mi-temps)\s+du\s+match"
)
_LIVE_TEXT = re.compile(r"(?i)\ben direct\b")

# Compétitions jouées aux horaires européens : aucun coup d'envoi avant ~11h
_EURO_COMP = re.compile(
    r"(?i)(ligue 1|ligue 2|\bnational\b|premier league|championship|league (one|two)|fa cup|"
    r"efl|carabao|\bliga\b|segunda|copa del rey|serie [ab]\b|coppa italia|bundesliga|dfb|"
    r"eredivisie|pro league|portugal|s[uü]per lig|super league|challenge league|"
    r"ligue des champions|ligue europa|ligue conf|champions league|europa league|"
    r"conference league|coupe de france|premiership|scottish|arkema|top 14|pro d2|"
    r"champions cup|challenge cup|starligue|euroligue|betclic|nations league|ligue des nations)"
)
_NON_EURO_COMP = re.compile(
    r"(?i)(nba|nfl|mlb|nhl|mls|wnba|libertadores|sudamericana|brasil|mexic|liga mx|"
    r"argentin|profesional|wxv|super rugby|rugby championship|a-league|j-?league|k ?league|"
    r"concacaf|copa america|nouvelle-z[eé]lande|australie|afrique du sud|provinces)"
)
EARLIEST_EURO_HOUR = 11

# Saison citée dans le texte (« … Ligue 1 McDonald's 2025/26 … ») : si ce n'est pas
# la saison en cours, c'est une rediffusion d'archive (« classique »).
# On ne retient que « … 2025/26 opposant X et Y » : les descriptions génériques de
# chaîne citent d'autres saisons (« … Ligue 1 McDonald's à partir de la saison 2024/2025 »).
_SEASON = re.compile(r"\b(20\d{2})\s*[/-]\s*(?:20)?(\d{2})\s+(?:opposant|oppose)\b")
# Numéro de journée : « 8e journée », « 30ème journée », « Journée 8 »
_ROUND = re.compile(r"(?i)(?:(\d{1,2})\s*(?:e|è?me|ère|ere|er|re)\s+journ|journ[ée]e\s+(\d{1,2})\b)")


# ───────────────────────── utilitaires ─────────────────────────

def _sport(e: SportEvent) -> str:
    return e.sport.value if hasattr(e.sport, "value") else str(e.sport)


def _alnum(s: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]", "", fold(s or ""))


def _paris(dt: datetime) -> datetime:
    return dt.astimezone(PARIS)


def _minutes(e: SportEvent) -> float:
    return (e.end - e.start).total_seconds() / 60


def _variant(e: SportEvent) -> str:
    """Distingue la version féminine / jeunes d'une même affiche."""
    text = fold(f"{e.competition or ''} {e.title} {e.subtitle or ''}")
    v = ""
    if re.search(r"arkema|feminin|women|\bwsl\b|liga f|frauen|\bd1 f", text):
        v += "w"
    m = re.search(r"\bu ?(\d\d)\b", text)
    if m:
        v += "u" + m.group(1)
    return v


def _round_no(e: SportEvent) -> str:
    m = _ROUND.search(f"{e.subtitle or ''} {e.description or ''} {e.title}")
    return (m.group(1) or m.group(2)) if m else ""


def _season_is_past(e: SportEvent, now: datetime) -> bool:
    """Le texte cite une saison antérieure à la saison en cours → archive."""
    current_start = now.year if now.month >= 7 else now.year - 1
    m = _SEASON.search(f"{e.description or ''} {e.subtitle or ''}")
    return bool(m) and int(m.group(1)) < current_start


def _cluster_key(e: SportEvent) -> Optional[str]:
    """Clé « même rencontre » (duo d'équipes). None si pas de duo identifiable."""
    if e.team1 and e.team2:
        a, b = sorted([_alnum(e.team1.name), _alnum(e.team2.name)])
        if a and b:
            return f"{_sport(e)}|{a}|{b}|{_variant(e)}|{_round_no(e)}"
    return None


def _is_euro_hours_competition(e: SportEvent) -> bool:
    if _sport(e) not in TEAM_SPORTS:
        return False
    text = f"{e.competition or ''} {e.title} {e.subtitle or ''}"
    return bool(_EURO_COMP.search(text)) and not _NON_EURO_COMP.search(text)


def _round_up_quarter(dt: datetime) -> datetime:
    base = dt.replace(second=0, microsecond=0)
    if dt.second or dt.microsecond:
        base += timedelta(minutes=1)
    add = (-base.minute) % 15
    return base + timedelta(minutes=add)


def estimate_kickoff(start: datetime) -> tuple[datetime, str]:
    """Coup d'envoi probable d'après le début de diffusion (sport collectif)."""
    q = _round_up_quarter(start)
    if timedelta(0) < q - start <= timedelta(minutes=10):
        return q, "estimate"
    return start, "estimate"


# ───────────────────────── étape ESPN ─────────────────────────

def _match_fixture(e: SportEvent, fixtures: Sequence[Fixture]):
    """
    Retourne (statut, fixture) :
      ("live", fx)    diffusion dans la fenêtre du coup d'envoi officiel
      ("replay", fx)  le match a eu lieu avant le début de cette diffusion
      ("unknown", None)
    """
    if not (e.team1 and e.team2) or not fixtures:
        return "unknown", None
    candidates = [f for f in fixtures if fixture_matches(e.team1.name, e.team2.name, f)]
    if not candidates:
        return "unknown", None

    start_utc = e.start.astimezone(timezone.utc)
    in_window = [
        f for f in candidates
        if f.start - BEFORE_KICKOFF <= start_utc <= f.start + AFTER_KICKOFF
    ]
    if in_window:
        # le coup d'envoi le plus proche d'un début d'antenne « normal » (≈ 10 min avant)
        best = min(in_window, key=lambda f: abs((f.start - start_utc) - timedelta(minutes=10)))
        return "live", best
    past = [f for f in candidates if f.start + AFTER_KICKOFF < start_utc]
    if past:
        return "replay", max(past, key=lambda f: f.start)
    return "unknown", None


# ───────────────────────── pipeline ─────────────────────────

def refine_events(
    events: Sequence[SportEvent],
    fixtures: Optional[Sequence[Fixture]] = None,
    now: Optional[datetime] = None,
) -> tuple[list[SportEvent], dict]:
    """Retourne (événements affinés, statistiques)."""
    fixtures = list(fixtures or [])
    now = now or datetime.now(timezone.utc)
    stats: Counter = Counter()

    kept: list[SportEvent] = []
    espn_ok: set[str] = set()          # ids confirmés « direct » par le calendrier officiel

    # 1 + 2 : filtres sans calendrier, puis calendrier officiel
    for src in events:
        e = src.model_copy(deep=True)
        sport = _sport(e)

        min_dur = MIN_DURATION.get(sport)
        if min_dur and _minutes(e) < min_dur:
            stats["drop_short"] += 1
            continue

        text = f"{e.title} {e.subtitle or ''} {e.description or ''}"
        if _REPLAY_TEXT.search(text) and not _LIVE_TEXT.search(text):
            stats["drop_replay_text"] += 1
            continue

        if _season_is_past(e, now):
            stats["drop_replay_season"] += 1
            continue

        status, fx = _match_fixture(e, fixtures) if sport in ("football", "basket") else ("unknown", None)
        if status == "replay":
            stats["drop_replay_espn"] += 1
            continue
        if status == "live" and fx is not None:
            e.kickoff = fx.start.astimezone(PARIS)
            e.kickoff_source = "espn"
            espn_ok.add(e.id)
            stats["espn_matched"] += 1

        kept.append(e)

    # 3a : horaires européens (heuristique, seulement si pas confirmé par ESPN)
    after_night: list[SportEvent] = []
    for e in kept:
        if (e.id not in espn_ok and _is_euro_hours_competition(e)
                and _paris(e.start).hour < EARLIEST_EURO_HOUR):
            stats["drop_replay_night"] += 1
            continue
        after_night.append(e)

    # 3b : même duo diffusé plusieurs fois → seule la 1re vague est le direct
    clusters: dict[str, list[SportEvent]] = defaultdict(list)
    for e in after_night:
        k = _cluster_key(e)
        if k:
            clusters[k].append(e)

    drop_ids: set[str] = set()
    for group in clusters.values():
        group.sort(key=lambda x: x.start)
        ref = group[0].start
        for e in group[1:]:
            if e.id in espn_ok:
                continue
            if e.start - ref > LIVE_WAVE:
                drop_ids.add(e.id)
                stats["drop_replay_wave"] += 1
    result = [e for e in after_night if e.id not in drop_ids]

    # 4 : coup d'envoi — calendrier officiel d'abord, estimation sinon
    by_cluster: dict[str, list[SportEvent]] = defaultdict(list)
    for e in result:
        k = _cluster_key(e)
        if k:
            by_cluster[k].append(e)

    for group in by_cluster.values():
        official = [e.kickoff for e in group if e.kickoff_source == "espn" and e.kickoff]
        if official:
            ko = Counter(official).most_common(1)[0][0]
            for e in group:
                if e.kickoff_source != "espn" and abs(e.start - ko) <= BEFORE_KICKOFF:
                    e.kickoff, e.kickoff_source = ko, "espn"
            continue
        if _sport(group[0]) not in TEAM_SPORTS:
            continue
        guesses = [estimate_kickoff(e.start)[0] for e in group]
        ko = Counter(guesses).most_common(1)[0][0]
        for e in group:
            e.kickoff, e.kickoff_source = _paris(ko), "estimate"
            stats["kickoff_estimated"] += 1

    # Équipes inconnues : estimation individuelle pour les sports collectifs
    for e in result:
        if e.kickoff is None and _sport(e) in TEAM_SPORTS and _cluster_key(e) is None:
            ko, _ = estimate_kickoff(e.start)
            e.kickoff, e.kickoff_source = _paris(ko), "estimate"

    # Cohérence : le coup d'envoi ne peut pas sortir de la diffusion
    for e in result:
        if e.kickoff and not (e.start - timedelta(minutes=1) <= e.kickoff <= e.end):
            e.kickoff, e.kickoff_source = None, None
        ref_time = e.kickoff or e.start
        if now > e.end:
            e.status = EventStatus.FINISHED
        elif now >= ref_time:
            e.status = EventStatus.LIVE
        else:
            e.status = EventStatus.UPCOMING

    result.sort(key=lambda x: (x.kickoff or x.start, x.start))
    stats["in"] = len(events)
    stats["out"] = len(result)
    return result, dict(stats)


# ───────────────────────── matchs en streaming (hors flux TV) ─────────────────────────
# Certains championnats ne passent plus sur une chaîne linéaire : le flux TV (XMLTV)
# n'en contient alors qu'une partie. Pour ces compétitions on complète avec le
# calendrier officiel et les plateformes qui les diffusent.
#   LaLiga 2026-2029 : les 380 matchs de la saison en direct sur DAZN **et** Disney+
#   (annonce des droits France ; plus de diffusion beIN Sports).
STREAMING_LEAGUES = {
    "esp.1": {
        "competition": "Liga",
        "platforms": [
            Channel(id="dazn.stream.fr", name="DAZN", slug="dazn", is_free=False),
            Channel(id="disney-plus.stream.fr", name="Disney+", slug="disney-plus", is_free=False),
        ],
    },
}
_FIXTURE_DURATION = timedelta(minutes=110)


def _fixture_entity(names: list[str]) -> Entity:
    ent = Entity(name=names[0] if names else "?", type=EntityType.CLUB)
    try:
        from .entity_registry import enrich_entity
        enriched = enrich_entity(ent.model_dump(), "football") or {}
        return Entity(**{k: v for k, v in enriched.items() if k in Entity.model_fields})
    except Exception:  # l'enrichissement (logos) est un bonus
        return ent


def fixture_event(fx: Fixture, channel: Channel, competition: str, now: datetime) -> SportEvent:
    """Évènement synthétique pour une rencontre du calendrier officiel."""
    start = fx.start.astimezone(PARIS)
    end = start + _FIXTURE_DURATION
    status = EventStatus.FINISHED if now > end else EventStatus.LIVE if now >= start else EventStatus.UPCOMING
    home, away = _fixture_entity(fx.home), _fixture_entity(fx.away)
    return SportEvent(
        id=hashlib.md5(f"espn-{fx.league}-{fx.id}-{channel.slug}".encode()).hexdigest()[:12],
        sport=SportType.FOOTBALL,
        competition=competition,
        title=f"{home.name} / {away.name}",
        team1=home, team2=away,
        channel=channel,
        start=start, end=end, status=status,
        kickoff=start, kickoff_source="espn",
    )


def _same_platform(e: SportEvent, channel: Channel) -> bool:
    return (e.channel.slug or "").split("-")[0] == channel.slug.split("-")[0]


def streaming_fixtures(events: Sequence[SportEvent], fixtures: Sequence[Fixture],
                       now: Optional[datetime] = None) -> list[SportEvent]:
    """Rencontres des compétitions streamées absentes du flux TV, une par plateforme."""
    now = now or datetime.now(timezone.utc)
    horizon_past = now - timedelta(hours=3)
    out: list[SportEvent] = []
    for fx in fixtures:
        cfg = STREAMING_LEAGUES.get(fx.league)
        if not cfg or fx.state == "post" or fx.start < horizon_past:
            continue
        for channel in cfg["platforms"]:
            found = any(
                e.team1 and e.team2 and _same_platform(e, channel)
                and abs((e.kickoff or e.start) - fx.start) <= timedelta(hours=6)
                and fixture_matches(e.team1.name, e.team2.name, fx)
                for e in events
            )
            if not found:
                out.append(fixture_event(fx, channel, cfg["competition"], now))
    return out
