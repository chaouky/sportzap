"""
SportZap — Calendrier officiel des rencontres (coups d'envoi).

Le XMLTV donne l'heure de début de la *diffusion* (avant-match inclus), pas
celle du coup d'envoi. Pour le football (+ NFL, NBA) on interroge les scoreboards
publics d'ESPN (JSON, sans clé) : ils donnent l'heure officielle, en UTC, de
chaque match.

Tout est « best effort » : si ESPN ne répond pas, ou si un match n'est pas
reconnu, l'export continue avec les heuristiques de `schedule_refine`.
"""
from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Iterable

import httpx

logger = logging.getLogger(__name__)

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"

# (sport ESPN, compétition). Vérifié le 24/10/2026 : tous répondent 200.
# NB : ESPN refuse les plages de dates (« dates=A-B » → 400) : on interroge jour par jour.
ESPN_COMPETITIONS: list[tuple[str, str]] = [
    *[("soccer", lg) for lg in (
        "fra.1", "fra.2", "fra.3", "fra.coupe_de_france", "fra.w.1",
        "eng.1", "eng.2", "eng.3", "eng.fa", "eng.league_cup",
        "esp.1", "esp.2", "esp.copa_del_rey",
        "ita.1", "ita.2", "ita.coppa_italia",
        "ger.1", "ger.2", "ger.dfb_pokal",
        "ned.1", "bel.1", "por.1", "tur.1", "sco.1", "sui.1",
        "uefa.champions", "uefa.europa", "uefa.europa.conf", "uefa.nations",
    )],
    ("football", "nfl"),
    ("basketball", "nba"),
]


@dataclass
class Fixture:
    start: datetime                      # coup d'envoi officiel (aware, UTC)
    home: list[str]                      # variantes de nom de l'équipe à domicile
    away: list[str]                      # idem à l'extérieur
    league: str = ""
    state: str = "pre"                   # pre | in | post
    id: str = ""


# ───────────────────────── parsing ─────────────────────────

def _parse_espn_date(raw: str) -> datetime:
    """'2026-10-24T19:00Z' | '2026-10-24T19:00:00Z' | '...+00:00' → aware UTC."""
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # Python < 3.11 n'accepte pas « THH:MM+00:00 » sans secondes
    if re.search(r"T\d{2}:\d{2}[+-]\d{2}:\d{2}$", s):
        s = re.sub(r"T(\d{2}:\d{2})([+-])", r"T\1:00\2", s)
    dt = datetime.fromisoformat(s)
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _team_names(team: dict) -> list[str]:
    names = [team.get("displayName"), team.get("shortDisplayName"),
             team.get("location"), team.get("name")]
    seen, out = set(), []
    for n in names:
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def parse_scoreboard(data: dict, league: str = "") -> list[Fixture]:
    """Transforme la réponse JSON d'un scoreboard ESPN en liste de Fixture."""
    fixtures: list[Fixture] = []
    for ev in data.get("events", []) or []:
        try:
            comp = (ev.get("competitions") or [{}])[0]
            competitors = comp.get("competitors") or []
            home = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not home or not away:
                continue
            state = ((ev.get("status") or {}).get("type") or {}).get("state", "pre")
            fixtures.append(Fixture(
                start=_parse_espn_date(ev["date"]),
                home=_team_names(home.get("team") or {}),
                away=_team_names(away.get("team") or {}),
                league=league,
                state=state,
                id=str(ev.get("id", "")),
            ))
        except (KeyError, ValueError, TypeError) as e:
            logger.debug("ESPN: évènement ignoré (%s)", e)
    return fixtures


# ───────────────────────── réseau ─────────────────────────

async def _fetch_day(client: httpx.AsyncClient, sem: asyncio.Semaphore,
                     sport: str, league: str, day: date) -> list[Fixture]:
    url = ESPN_SCOREBOARD.format(sport=sport, league=league)
    async with sem:
        resp = await client.get(url, params={"dates": f"{day:%Y%m%d}"})
    resp.raise_for_status()
    return parse_scoreboard(resp.json(), league)


async def fetch_fixtures(
    first_day: date,
    last_day: date,
    competitions: Iterable[tuple[str, str]] = ESPN_COMPETITIONS,
    timeout: float = 20.0,
) -> list[Fixture]:
    """Récupère les rencontres de toutes les compétitions sur [first_day, last_day]."""
    competitions = list(competitions)
    days = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
    sem = asyncio.Semaphore(12)
    jobs = [(sp, lg, d) for sp, lg in competitions for d in days]
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "SportZap/1.0"}) as client:
        results = await asyncio.gather(
            *(_fetch_day(client, sem, sp, lg, d) for sp, lg, d in jobs),
            return_exceptions=True,
        )
    seen: dict[str, Fixture] = {}
    ok = 0
    for (sp, lg, d), res in zip(jobs, results):
        if isinstance(res, Exception):
            logger.debug("ESPN %s/%s %s indisponible : %s", sp, lg, d, res)
            continue
        ok += 1
        for fx in res:
            seen[fx.id or f"{lg}{fx.start}{fx.home}"] = fx
    logger.info("ESPN: %d/%d requêtes OK, %d rencontres", ok, len(jobs), len(seen))
    return list(seen.values())


# ───────────────────────── rapprochement des noms ─────────────────────────

def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


# Noms français / formes TV → forme ESPN
_ALIASES = {
    "paris sg": "paris saint germain", "psg": "paris saint germain",
    "naples": "napoli", "seville": "sevilla", "cologne": "koln",
    "francfort": "frankfurt", "breme": "bremen", "hambourg": "hamburg",
    "mayence": "mainz", "augsbourg": "augsburg", "nuremberg": "nurnberg",
    "munich": "bayern munich", "bale": "basel", "berne": "bern",
    "bruges": "club brugge", "anvers": "antwerp", "gand": "gent",
    "la gantoise": "gent", "malines": "mechelen", "courtrai": "kortrijk",
    "la corogne": "deportivo la coruna", "bergame": "atalanta",
    "fribourg": "freiburg", "betis seville": "real betis",
}
_TOKEN_ALIASES = {k: v for k, v in _ALIASES.items() if " " not in k}

# Mots sans pouvoir discriminant (préfixes/suffixes de clubs)
_NOISE = {"fc", "cf", "ac", "as", "sc", "afc", "ssc", "us", "rc", "ogc", "fk", "sv", "vfb",
          "vfl", "fsv", "tsg", "sk", "kv", "kaa", "de", "la", "le", "el", "the", "1", "05",
          "football", "club", "calcio", "olympique", "stade", "association", "sporting"}


@lru_cache(maxsize=None)
def _tokens(name: str) -> frozenset[str]:
    f = fold(name)
    f = _ALIASES.get(f, f)
    out: set[str] = set()
    for t in f.split():
        if t in _NOISE or len(t) <= 1:
            continue
        out.update(_TOKEN_ALIASES.get(t, t).split())
    return frozenset(out - _NOISE)


def _close(x: str, y: str) -> bool:
    """Deux mots « proches » : égaux ou même racine (lyon/lyonnais, valence/valencia)."""
    if x == y:
        return True
    m = min(len(x), len(y))
    if m < 4:
        return False
    cp = 0
    for a, b in zip(x, y):
        if a != b:
            break
        cp += 1
    return cp >= 4 and cp >= 0.6 * m


def _covered(small: frozenset[str], big: frozenset[str]) -> bool:
    return bool(small) and all(any(_close(x, y) for y in big) for x in small)


def name_score(tv_name: str, espn_names) -> float:
    """Similarité 0..1 entre le nom vu à la TV et les variantes ESPN."""
    return _name_score(tv_name, tuple(espn_names))


@lru_cache(maxsize=None)
def _name_score(tv_name: str, espn_names: tuple) -> float:
    tv_tok = _tokens(tv_name)
    if not tv_tok:
        return 0.0
    best = 0.0
    for n in espn_names:
        es_tok = _tokens(n)
        if not es_tok:
            continue
        if tv_tok == es_tok:
            return 1.0
        small, big = (tv_tok, es_tok) if len(tv_tok) <= len(es_tok) else (es_tok, tv_tok)
        # « Manchester City » ⊄ « Manchester United » : tous les mots du plus court
        # doivent avoir un équivalent dans le plus long
        if _covered(small, big) and (len(small) >= 2 or len(big) <= 2):
            best = max(best, 0.9)
            continue
        flat_a, flat_b = "".join(sorted(tv_tok)), "".join(sorted(es_tok))
        best = max(best, SequenceMatcher(None, flat_a, flat_b).ratio() * 0.95)
    return best


MIN_NAME_SCORE = 0.78


def fixture_matches(team1: str, team2: str, fx: Fixture) -> bool:
    """Vrai si {team1, team2} correspond à {home, away} (dans un sens ou l'autre)."""
    a = min(name_score(team1, fx.home), name_score(team2, fx.away))
    b = min(name_score(team1, fx.away), name_score(team2, fx.home))
    return max(a, b) >= MIN_NAME_SCORE
