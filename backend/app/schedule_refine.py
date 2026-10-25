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
  5. sports sans équipes (F1, cyclisme, ski, MotoGP, escalade, judo…) :
       - F1 : chaque séance (essais, qualifications, course) est rapprochée du
         calendrier officiel (ESPN) ; une diffusion qui commence après la séance
         est une rediffusion ;
       - sinon, une même épreuve n'a qu'un direct : la 1re diffusion plausible
         (cyclisme : ≥ 100 min, de jour ; ski : de jour) et ses simulcasts à
         ≤ 75 min ; les repassages suivants sont écartés.
"""
from __future__ import annotations

import hashlib
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

from .fixtures import Fixture, Session, fixture_matches, fold
from .models import Channel, Entity, EntityType, EventStatus, SportEvent, SportType

logger = logging.getLogger(__name__)

PARIS = ZoneInfo("Europe/Paris")

TEAM_SPORTS = {"football", "rugby", "handball", "basket", "volleyball", "foot_us"}
# Durée minimale d'une vraie diffusion de match (minutes) — en dessous :
# avant-match, flash, résumé.
MIN_DURATION = {"football": 75, "rugby": 75, "handball": 55, "basket": 60, "volleyball": 55, "foot_us": 100}

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


def _cluster_key(e: SportEvent, with_round: bool = True) -> Optional[str]:
    """Clé « même rencontre » (duo d'équipes). None si pas de duo identifiable."""
    if e.team1 and e.team2:
        a, b = sorted([_alnum(e.team1.name), _alnum(e.team2.name)])
        if a and b:
            rnd = _round_no(e) if with_round else ""
            return f"{_sport(e)}|{a}|{b}|{_variant(e)}|{rnd}"
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


# ───────────────────────── F1 : séances officielles ─────────────────────────

SESSION_BEFORE = timedelta(minutes=90)    # l'antenne s'ouvre avant la séance (avant-show)
SESSION_AFTER = timedelta(minutes=15)

_F1_ACADEMY = re.compile(r"\b(?:f1 academy|feature race|(?:1re|1ere|2e|2eme|premiere|deuxieme) course)\b")


def f1_session_kind(e: SportEvent) -> str:
    """Type de séance d'après le titre français ('' = inconnu / F1 Academy)."""
    text = fold(f"{e.title} {e.subtitle or ''}")
    if _F1_ACADEMY.search(text):
        return ""
    m = re.search(r"\bessais libres (\d)\b", text)
    if m:
        return f"FP{m.group(1)}"
    if re.search(r"qualifications? sprint|sprint shootout|essais qualificatifs sprint", text):
        return "SQ"
    if re.search(r"course sprint|\bsprint\b", text):
        return "Sprint"
    if re.search(r"essais qualificatifs|\bqualifications?\b", text):
        return "Qual"
    if re.search(r"\bcourse\b", text):
        return "Race"
    return ""


def _match_session(e: SportEvent, kind: str, sessions: Sequence[Session]):
    """('live', s) | ('replay', s) | ('unknown', None)"""
    cands = [x for x in sessions if x.kind == kind]
    start = e.start.astimezone(timezone.utc)
    live = [x for x in cands if x.start - SESSION_BEFORE <= start <= x.start + SESSION_AFTER]
    if live:
        return "live", min(live, key=lambda x: abs(x.start - start))
    past = [x for x in cands if x.start + SESSION_AFTER < start]
    if past:
        return "replay", max(past, key=lambda x: x.start)
    return "unknown", None


# ───────────────────────── sports sans équipes ─────────────────────────

SOLO_WAVE = timedelta(minutes=75)         # simulcast d'un même direct (Eurosport 1 + 360…)
TENNIS_WAVE = timedelta(hours=7)         # journée de tennis : blocs successifs d'un même tour
_SOLO_OTHER_TITLE = re.compile(
    r"(?i)escalade|judo|patinage|biathlon|saut [àa] ski|gymnastique|snooker|padel|rallye|"
    r"curling|\btrail\b|endurance|cyclo-?cross|squash|badminton|billard|tennis de table|"
    r"speedway|[ée]quitation"
)
# Épreuves dont le direct tombe la nuit ou tôt le matin en France
_OVERNIGHT_OK = re.compile(
    r"(?i)australi|down under|chine\b|china|guangxi|japon|japan|cor[ée]e|nouvelle-z[ée]lande|"
    r"p[ée]kin|beijing|zhangjiakou|perisher|cardrona|wanaka|ushuaia|santiago|vancouver|"
    r"osaka|tokyo|ningbo|wuhan|guangzhou|shanghai|hong ?kong|s[ée]oul|seoul|macao|riyad|"
    r"phillip island|sepang|malaisie|thaïlande|thailande|buriram|mandalika|indon[ée]sie"
)
_ROUND_TOKEN = re.compile(
    r"(?i)((?:\d+\s*(?:er|re|ère|e)\s+)?(?:tour|jour|manche|demi[- ]?finales?|finale)(?:\s+(?:dames|messieurs|hommes|femmes|mixte))?"
    r"|\d+\s*(?:er|re|ère|e)\s+(?:tour|jour|manche)|\d+e\s+de\s+finale|quarts?\s+de\s+finale)"
)
# Une finale / demi-finale se joue en un seul jour : tout repassage ultérieur est une rediffusion
_ONE_DAY_ROUND = re.compile(r"(?i)^(?:\d+\s*(?:er|re|ère|e)\s+)?(?:demi[- ]?finales?|finale)\b")
_GENERIC_TENNIS_SUB = re.compile(r"(?i)^(?:tennis|wta[^.]*|atp[^.]*|[a-zà-ÿ' -]{3,25})\.?$")
_MOTOR_SESSIONS = (
    (r"warm\s*up", "warmup"),
    (r"feature race", "feature"),
    (r"(\d+)\s*(?:re|er|e|ere)\s+course", "course#"),
    (r"sprint race", "sprintrace"),
    (r"sprint", "sprint"),
    (r"qualificatifs?|qualifications?", "qualif"),
    (r"essais?\s+libres?\s*(\d)", "fp#"),
    (r"essais?", "essais"),
    (r"course", "course"),
)


def _motor_session_key(e: SportEvent, family: str) -> Optional[str]:
    """Une même séance d'un Grand Prix (F1, F1 Academy, MotoGP, Moto2, Moto3) n'a qu'un
    direct, quels que soient les libellés de chaque rediffusion (« La course des Moto 3 »,
    « Formule 1 : GP… La course. Championnat du monde. »…). Sert aussi quand ESPN est
    injoignable : la 1re diffusion du flux est alors le direct."""
    if not e.competition:
        return None
    prefix = fold((e.title or "").split(":")[0])
    if family == "motogp":
        cls = re.search(r"\bmoto ?(gp|2|3)\b", fold(f"{e.title} {e.subtitle or ''}"))
        if not cls:
            return None
        klass = cls.group(1)
    else:
        klass = "academy" if "academy" in prefix or re.search(
            r"feature race|\d+\s*(?:re|er|e)\s+course|sprint race", fold(f"{e.title} {e.subtitle or ''}")) else "f1"
    # le nom du Grand Prix est répété dans le sous-titre : on le retire avant de lire la séance
    sub = fold(e.subtitle or "").replace(fold(e.competition), " ")
    for pattern, name in _MOTOR_SESSIONS:
        m = re.search(pattern, sub)
        if m:
            num = m.group(1) if name.endswith("#") and m.groups() else ""
            return f"{family}|{_alnum(e.competition)}|{klass}|{name.rstrip('#')}{num}"
    return None


def _round_text(e: SportEvent) -> str:
    # on cherche dans le sous-titre après le nom de l'épreuve (« …Cup. 1er tour. »)
    candidates = [m.group(1) for m in _ROUND_TOKEN.finditer(fold(e.subtitle or ""))]
    candidates = [c for c in candidates if not re.fullmatch(r"(?:tour|jour|manche)", c.strip())]
    return candidates[0].strip() if candidates else ""


def _round_of(e: SportEvent) -> str:
    return _alnum(_round_text(e))


def _solo_family(e: SportEvent) -> Optional[str]:
    sp = _sport(e)
    if sp in ("cyclisme", "ski", "motogp", "f1"):
        return sp
    if sp in ("golf", "voile", "equitation"):
        return "session"
    if sp == "tennis" and not (e.team1 and e.team2):
        return "tennis"
    if sp == "other" and not (e.team1 and e.team2) and _SOLO_OTHER_TITLE.search(e.title or ""):
        return "session"
    return None


def _solo_plausible(e: SportEvent, family: str) -> bool:
    """Cette diffusion peut-elle être le direct ? (les repassages tombent la nuit / sont courts)"""
    p = _paris(e.start)
    hour = p.hour + p.minute / 60
    overnight = bool(_OVERNIGHT_OK.search(f"{e.title} {e.subtitle or ''} {e.description or ''}"))
    if family == "cyclisme":
        return _minutes(e) >= 100 and (overnight or 7.5 <= hour < 23.5)
    if family == "ski":
        return overnight or 7 <= hour < 22
    generic = bool(_GENERIC_TENNIS_SUB.match((e.subtitle or "").strip()))
    if family == "tennis":
        # bandeaux « Eurosport 360 » = courts annexes, doublons des chaînes principales
        if e.channel.slug == "eurosport-360" and generic:
            return False
        return overnight or 6.5 <= hour < 24
    if family == "session":
        if e.channel.slug == "eurosport-360" and generic:
            return False
        # le golf américain se joue la nuit en France ; le reste, de jour
        if _sport(e) != "golf":
            return overnight or 7.5 <= hour < 24
    return True


def _solo_key(e: SportEvent, family: str) -> str:
    if family in ("motogp", "f1"):
        k = _motor_session_key(e, family)
        if k:
            return k
    if family == "session":
        rnd = _round_of(e)
        comp = _alnum(e.competition or e.title)
        if rnd and (_sport(e) == "golf" or _ONE_DAY_ROUND.match(_round_text(e))):
            return f"session|{_sport(e)}|{comp}|{rnd}"
        # un jour = une séance de l'après-midi + une séance du soir
        p = _paris(e.start)
        half = "a" if p.hour < 17 else "p"
        return f"session|{_sport(e)}|{comp}|{rnd}|{p.date().isoformat()}|{half}"
    if family == "tennis":
        rnd = _round_of(e)
        if rnd:
            # même tour sur la même chaîne : le direct du jour + ses blocs successifs ;
            # les passages des jours suivants sont des rediffusions (cf. TENNIS_WAVE)
            return f"tennis|{e.channel.slug}|{_alnum(e.competition or e.title)}|{rnd}"
        # sans tour : blocs successifs légitimes, on ne filtre que les horaires implausibles
        return f"tennis|{e.id}"
    return f"{family}|{_alnum(e.title)}|{_alnum(e.subtitle)}"


# ───────────────────────── pipeline ─────────────────────────

def refine_events(
    events: Sequence[SportEvent],
    fixtures: Optional[Sequence[Fixture]] = None,
    now: Optional[datetime] = None,
    sessions: Optional[Sequence[Session]] = None,
) -> tuple[list[SportEvent], dict]:
    """Retourne (événements affinés, statistiques)."""
    fixtures = list(fixtures or [])
    sessions = list(sessions or [])
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

        if sport == "f1" and sessions:
            kind = f1_session_kind(e)
            if kind:
                sstatus, sess = _match_session(e, kind, sessions)
                if sstatus == "replay":
                    stats["drop_replay_session"] += 1
                    continue
                if sstatus == "live" and sess is not None:
                    e.kickoff = sess.start.astimezone(PARIS)
                    e.kickoff_source = "espn"
                    espn_ok.add(e.id)
                    stats["session_matched"] += 1

        status, fx = (_match_fixture(e, fixtures)
                      if sport in ("football", "basket", "foot_us") else ("unknown", None))
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

    # 3b : même duo diffusé plusieurs fois → seule la 1re vague est le direct.
    # Le numéro de journée n'est pas toujours renseigné (« 8e journée » sur la
    # rediffusion, rien sur le direct) : on regroupe d'abord sans lui, et on ne
    # sépare par journée que si deux journées différentes sont explicitement citées
    # (aller-retour sur la même semaine).
    pairs: dict[str, list[SportEvent]] = defaultdict(list)
    for e in after_night:
        k = _cluster_key(e, with_round=False)
        if k:
            pairs[k].append(e)

    drop_ids: set[str] = set()
    for group in pairs.values():
        rounds = {_round_no(e) for e in group} - {""}
        subgroups: list[list[SportEvent]]
        if len(rounds) >= 2:
            subgroups = [[e for e in group if _round_no(e) in (r, "")] for r in sorted(rounds)]
        else:
            subgroups = [group]
        for sub in subgroups:
            sub.sort(key=lambda x: x.start)
            ref = sub[0].start
            for e in sub[1:]:
                if e.id in espn_ok:
                    continue
                if e.start - ref > LIVE_WAVE:
                    if e.id not in drop_ids:
                        stats["drop_replay_wave"] += 1
                    drop_ids.add(e.id)
    result = [e for e in after_night if e.id not in drop_ids]

    # 3c : sports sans équipes — une épreuve n'a qu'un direct
    solo: dict[str, list[SportEvent]] = defaultdict(list)
    for e in result:
        fam = _solo_family(e)
        if fam and e.id not in espn_ok:
            solo[_solo_key(e, fam)].append(e)
    solo_drop: set[str] = set()
    for key, group in solo.items():
        fam = key.split("|", 1)[0]
        group.sort(key=lambda x: x.start)
        live = [x for x in group if _solo_plausible(x, fam)]
        ref = live[0].start if live else None
        for x in group:
            wave = TENNIS_WAVE if fam == "tennis" else SOLO_WAVE
            if ref is None or x not in live or x.start - ref > wave:
                solo_drop.add(x.id)
                stats["drop_replay_solo"] += 1
    result = [e for e in result if e.id not in solo_drop]

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
