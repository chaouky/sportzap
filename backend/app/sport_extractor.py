"""
SportZap — Sport Event Extractor

Takes raw XMLTV programmes and:
1. Filters to sport-only programmes
2. Classifies the sport type (football, rugby, tennis, etc.)
3. Extracts structured entities: competition, team1, team2
4. Generates unique IDs and normalized output

This is the brain of the pipeline. French TV sport titles follow
semi-predictable patterns which we exploit with regex + heuristics.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from typing import Optional

from .models import (
    Channel, Entity, EntityType, EventStatus,
    SportEvent, SportType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# SPORT CLASSIFICATION
# ═══════════════════════════════════════════════════════

# Category keywords → SportType mapping
# Priority order: more specific first
CATEGORY_MAP: list[tuple[list[str], SportType]] = [
    (["football", "foot", "soccer"], SportType.FOOTBALL),
    (["rugby"], SportType.RUGBY),
    (["tennis"], SportType.TENNIS),
    (["basket", "basketball", "basket-ball", "nba"], SportType.BASKET),
    (["formule 1", "f1", "sport mécanique", "sport mecanique", "auto-moto"], SportType.F1),
    (["motogp", "moto gp", "superbike", "motocyclisme"], SportType.MOTOGP),
    (["cyclisme", "vélo", "tour de france", "giro", "vuelta"], SportType.CYCLISME),
    (["mma", "ufc", "pfl", "combat", "sport de combat", "arts martiaux"], SportType.MMA),
    (["boxe", "boxing"], SportType.BOXE),
    (["handball", "hand-ball", "hand"], SportType.HANDBALL),
    (["natation", "swimming", "plongeon", "water-polo"], SportType.NATATION),
    (["athlétisme", "athletisme", "marathon"], SportType.ATHLETISME),
    (["ski", "biathlon", "sport d'hiver", "sports d'hiver", "patinage"], SportType.SKI),
    (["golf"], SportType.GOLF),
    (["voile", "sailing", "nautisme"], SportType.VOILE),
    (["équitation", "equitation", "hippisme"], SportType.EQUITATION),
    (["volley", "volleyball", "volley-ball"], SportType.VOLLEYBALL),
]

# Title-based patterns for when categories are vague ("sport" only)
TITLE_SPORT_PATTERNS: list[tuple[str, SportType]] = [
    (r"(?i)\bfoot(?:ball)?\b", SportType.FOOTBALL),
    (r"(?i)\brugby\b", SportType.RUGBY),
    (r"(?i)\btennis\b", SportType.TENNIS),
    (r"(?i)\bbasket(?:ball|[\s-]ball)?\b", SportType.BASKET),
    (r"(?i)\b(?:nba)\b", SportType.BASKET),
    (r"(?i)\b(?:formule\s*1|f1|grand\s*prix)\b", SportType.F1),
    (r"(?i)\b(?:motogp|moto\s*gp|superbike)\b", SportType.MOTOGP),
    (r"(?i)\b(?:cyclisme|tour\s+de|étape|giro|vuelta)\b", SportType.CYCLISME),
    (r"(?i)\b(?:mma|ufc|pfl|cage\s*warriors)\b", SportType.MMA),
    (r"(?i)\b(?:boxe|boxing)\b", SportType.BOXE),
    (r"(?i)\bhandball\b", SportType.HANDBALL),
    (r"(?i)\b(?:natation|swimming)\b", SportType.NATATION),
    (r"(?i)\b(?:athlétisme|athletisme)\b", SportType.ATHLETISME),
    (r"(?i)\b(?:ski|biathlon|slalom|descente)\b", SportType.SKI),
    (r"(?i)\bgolf\b", SportType.GOLF),
    (r"(?i)\b(?:voile|sailing)\b", SportType.VOILE),
    (r"(?i)\bvolley(?:ball|[\s-]ball)?\b", SportType.VOLLEYBALL),
]

# Known sport keywords that confirm a programme is sport
SPORT_CATEGORY_KEYWORDS = {
    "sport", "football", "rugby", "tennis", "basket", "basket-ball",
    "basketball", "handball", "hand-ball", "cyclisme", "formule 1",
    "sport mécanique", "sport mecanique", "athlétisme", "athletisme",
    "natation", "golf", "voile", "ski", "biathlon", "boxe", "mma",
    "sport de combat", "sports de combat", "volley", "volleyball",
    "volley-ball", "hippisme", "équitation", "equitation",
    "sport d'hiver", "sports d'hiver", "auto-moto", "motocyclisme",
    "motogp", "catch",
}

# Title keywords that confirm sport even without category
SPORT_TITLE_KEYWORDS = [
    r"(?i)\b(?:ligue\s*[12]|liga|serie\s*a|bundesliga|premier\s*league)\b",
    r"(?i)\b(?:champions\s*league|ligue\s*des\s*champions|europa\s*league)\b",
    r"(?i)\b(?:top\s*14|pro\s*d2|champions\s*cup|coupe\s*d'europe)\b",
    r"(?i)\b(?:roland[\s-]*garros|wimbledon|us\s*open|open\s*d'australie)\b",
    r"(?i)\b(?:masters\s*1000|atp|wta)\b",
    r"(?i)\b(?:tour\s+de\s+france|giro|vuelta|paris[\s-]*roubaix)\b",
    r"(?i)\b(?:grand\s*prix|formule\s*1|f1)\b",
    r"(?i)\b(?:nba|nfl|nhl|mlb|betclic\s*[eé]lite)\b",
    r"(?i)\b(?:six\s*nations|golden\s*league|euro\s*\d{4}|coupe\s*du\s*monde)\b",
    r"(?i)\b(?:jeux\s*olympiques|jo\s*\d{4})\b",
    r"(?i)\b(?:ufc|pfl|bellator)\b",
]


def is_sport_programme(prog: dict) -> bool:
    """Determine if a raw XMLTV programme is sport-related."""
    categories = set(prog.get("categories", []))

    # Direct category match
    if categories & SPORT_CATEGORY_KEYWORDS:
        return True

    # Title-based detection
    title = prog.get("title", "") + " " + (prog.get("subtitle") or "")
    for pattern in SPORT_TITLE_KEYWORDS:
        if re.search(pattern, title):
            return True

    return False


# ── Match detection: patterns that strongly indicate a real sporting event ──

# "Sport : Competition | Team1 / Team2" — canonical French TV format
_COLON_MATCH = re.compile(
    r"(?i)^[^:]+\s*:\s*.+\s*[/|]\s*.+",  # "Football : Ligue 1 | PSG / OM"
)

# "Team1 / Team2" or "Team1 - Team2" (standalone matchup)
_SLASH_MATCH = re.compile(
    r"(?i)^[A-ZÀ-Ü0-9][^:/\n]{2,40}\s*(?:/|-)\s*[A-ZÀ-Ü0-9][^:/\n]{2,40}$"
)

# "Sport : Competition" with known competition keyword (match likely)
_COMPETITION_MATCH = re.compile(
    r"(?i)^[^:]+\s*:\s*("
    r"ligue\s*[12]|liga|serie\s*a|bundesliga|premier\s*league|eredivisie"
    r"|champions\s*(league|cup)|ligue\s*des\s*champions|europa\s*league"
    r"|conference\s*league|ligue\s*europa|coupe\s*(de\s*france|d'europe|d'angleterre|du\s*monde|gambardella)"
    r"|top\s*14|pro\s*d2|six\s*nations|super\s*rugby"
    r"|roland[\s-]*garros|wimbledon|us\s*open|masters?\s*(1000|de)"
    r"|tour\s+de|grand\s*prix|formule\s*[12]|motogp"
    r"|nba|betclic|golden\s*league|champions\s*cup"
    r"|ufc|pfl|bellator"
    r"|match\s*(amical|international|d'archives)"
    r"|[0-9a-z]+\s*(journée|[eè]tape|ronde|tour\b|finale|quart|demi)"
    r")"
)

# "Tennis: Player1 - Player2" or "Snooker: Player1 - Player2"
_INDIVIDUAL_MATCH = re.compile(
    r"(?i)^(tennis|snooker|golf|boxe|mma|judo|escrime|natation|athl[eé]tisme)\s*:\s*.+\s*[-/]\s*.+"
)

# Patterns that definitively mark NON-match content
_NON_MATCH = re.compile(
    r"(?i)("
    # Magazines / shows / talk
    r"\bmag\b|magazine|\bshow\b|hebdo|weekly|mensuel"
    r"|\bd[eé]brief\b|avant.match|après.match|mi.temps en \+"
    r"|plateau\b|conference de presse|conférence de presse"
    r"|best of|résumé|resume|temps forts|highlights|flashback|retro\b"
    r"|rediffusion|redif\b|replay\b|rerun\b|re-run\b|archive|d'archives"
    r"|différé|en différé|enregistré|enregistrement"
    r"|canal champions club|champions club|canal sport\b|canal nba"
    r"|dazn pro league|ligue 1 show|ligue 1 review|ligue 1 preview"
    r"|stade 2|stats my|sport flash|sportflash|zap.?sport|bein zap"
    r"|l'[eé]quipe (du soir|de greg|de choc)|l'oeil des pros"
    r"|pleine lucarne|grand direct|le bonus|le temps additionnel"
    r"|late football club|nba extra|soirée des champions"
    r"|liga extra|histoires de premier league|made in england"
    r"|complètement foot|passion foot|football nation"
    r"|le grand d[eé]brif|live :|retro :"
    # Channel branding / filler
    r"|eurosport 360 \d|ligue 1\+ \d+$"
    r"|programme (terminé|à venir)|a bientôt sur|vivez en direct"
    r"|beIN sports, le plus"
    # Betting / poker
    r"|pronos\b|pmu\b|poker|tiercé|quinté"
    # Documentary / adventure / nature
    r"|documentaire|reportage\b|portrait\b|interview\b"
    r"|aventure|exploration|voyage\b|nature\b"
    # Fitness / yoga
    r"|yoga|fitness\s*:"
    # Generics with no matchup info
    r"|^sport$|^sports$|^football$|^rugby$|^tennis$|^basket$"
    r")"
)


def is_actual_match(prog: dict) -> bool:
    """
    Return True only if the programme looks like an actual sporting event
    (a real match/race/fight), not a TV show, magazine, or branding filler.

    Strategy: whitelist strong match signals, blacklist known non-match patterns.
    """
    title = (prog.get("title") or "").strip()
    subtitle = (prog.get("subtitle") or "").strip()

    # Step 1: reject known non-match patterns
    if _NON_MATCH.search(title):
        return False

    # Reject specific false positives
    _FP = re.compile(
        r"(?i)("
        r"anchored in paradise|direct auto express|planete\+"
        r"|nautical channel|pré combat\b|format ufc"
        r"|d'archives|multiplex$|ça va frotter"
        r"|eva : league|mgg tv|valorant|esport|e-sport"
        r"|snooker\s*:\s*masters$"   # generic snooker show (no matchup)
        r"|carrousel\b|monde duplantis|fast.?zone"
        r"|uefa\s*:\s*ce que vous|roland.garros dans l'ombre"
        r"|on board moto|jour de match / jt"
        r"|dans le peloton|inside\b|behind the scenes"
        r"|[a-z] bientôt|programme terminé"
        r")"
    )
    if _FP.search(title):
        return False

    # Step 2: accept clear match formats
    combined = title + " " + subtitle

    if _COLON_MATCH.search(combined):        # "Football : Ligue 1 | PSG / OM"
        return True
    if _SLASH_MATCH.search(title):           # "PSG / OM" or "PSG - OM"
        return True
    if _COMPETITION_MATCH.search(title):     # "Football : Ligue des champions"
        return True
    if _INDIVIDUAL_MATCH.search(combined):   # "Tennis : Djokovic - Alcaraz"
        return True

    # Step 3: subtitle has a matchup → likely real event
    if subtitle and _SLASH_MATCH.search(subtitle):
        return True

    # Step 4: reject anything that didn't match a positive pattern
    return False


def classify_sport(prog: dict) -> SportType:
    """Classify the sport type from categories + title."""
    categories = prog.get("categories", [])
    title = prog.get("title", "") + " " + (prog.get("subtitle") or "")

    # 1. Try category-based classification
    for keywords, sport_type in CATEGORY_MAP:
        for cat in categories:
            if any(kw in cat for kw in keywords):
                return sport_type

    # 2. Fall back to title-based patterns
    for pattern, sport_type in TITLE_SPORT_PATTERNS:
        if re.search(pattern, title):
            return sport_type

    return SportType.OTHER


# ═══════════════════════════════════════════════════════
# ENTITY EXTRACTION (Teams, Players, Competitions)
# ═══════════════════════════════════════════════════════

# Country code lookup for national teams and player nationalities
COUNTRY_CODES = {
    "france": "fr", "danemark": "dk", "allemagne": "de", "espagne": "es",
    "italie": "it", "angleterre": "gb-eng", "pays de galles": "gb-wls",
    "galles": "gb-wls", "écosse": "gb-sct", "ecosse": "gb-sct",
    "irlande": "ie", "portugal": "pt", "belgique": "be", "pays-bas": "nl",
    "suisse": "ch", "autriche": "at", "pologne": "pl", "croatie": "hr",
    "serbie": "rs", "suède": "se", "norvège": "no", "finlande": "fi",
    "brésil": "br", "bresil": "br", "argentine": "ar", "usa": "us",
    "états-unis": "us", "etats-unis": "us", "japon": "jp", "corée": "kr",
    "australie": "au", "cameroun": "cm", "sénégal": "sn", "maroc": "ma",
    "algérie": "dz", "tunisie": "tn", "afrique du sud": "za",
    "mexique": "mx", "colombie": "co", "uruguay": "uy", "chili": "cl",
    "canada": "ca", "nouvelle-zélande": "nz", "roumanie": "ro",
    "grèce": "gr", "turquie": "tr", "russie": "ru", "ukraine": "ua",
    "république tchèque": "cz", "hongrie": "hu", "slovaquie": "sk",
    "grande-bretagne": "gb", "gbr": "gb", "srb": "rs", "esp": "es",
    "cmr": "cm", "fra": "fr", "den": "dk",
}

# Known national teams in sport context
NATIONAL_TEAM_NAMES = set(COUNTRY_CODES.keys())

# ISO-3 to ISO-2 for player nationality tags like (SRB), (ESP)
ISO3_TO_ISO2 = {
    "srb": "rs", "esp": "es", "fra": "fr", "gbr": "gb", "cmr": "cm",
    "ger": "de", "ita": "it", "bra": "br", "arg": "ar", "usa": "us",
    "jpn": "jp", "aus": "au", "ned": "nl", "por": "pt", "bel": "be",
    "sui": "ch", "aut": "at", "cro": "hr", "den": "dk", "swe": "se",
    "nor": "no", "pol": "pl", "cze": "cz", "rou": "ro", "gre": "gr",
    "hun": "hu", "svk": "sk", "irl": "ie", "wal": "gb-wls", "sco": "gb-sct",
    "rsa": "za", "mar": "ma", "alg": "dz", "tun": "tn", "sen": "sn",
    "mex": "mx", "col": "co", "uru": "uy", "chi": "cl", "can": "ca",
    "nzl": "nz", "tur": "tr", "ukr": "ua", "rus": "ru", "kor": "kr",
    "chn": "cn",
}

# Regex patterns for extracting matchups from subtitle
# French TV typically uses: "Team1 / Team2" or "Team1 - Team2" or "Team1 vs Team2"
MATCHUP_PATTERNS = [
    # "N. Djokovic (SRB) / C. Alcaraz (ESP)" — individual with nationality
    re.compile(
        r"^(?:.*?:\s*)?(?P<t1>.+?)\s*(?:/|vs\.?|contre)\s*(?P<t2>.+?)\s*$",
        re.IGNORECASE,
    ),
]

# Player name with nationality: "N. Djokovic (SRB)"
PLAYER_WITH_NAT = re.compile(
    r"(?P<name>[A-ZÀ-Ü][.\s]?\s*[A-ZÀ-Üa-zà-ü'-]+(?:\s+[A-ZÀ-Üa-zà-ü'-]+)*)"
    r"\s*\((?P<nat>[A-Z]{3})\)",
)

# Competition extraction from title
# Supports both ":" and " - " separators:
#   "Football : Ligue 1, 29e journée" → comp="Ligue 1, 29e journée"
#   "Football - Match Amical"         → comp="Match Amical"
#   "Rugby : Top 14, 22e journée"     → comp="Top 14 · J22"
TITLE_COMP_PATTERNS = [
    # "Sport : Competition" (most common, Télérama)
    re.compile(r"^(?P<sport>[^:]+?)\s*:\s*(?P<comp>.+)$"),
    # "Sport - Competition" (TF1 variant)
    re.compile(r"^(?P<sport>(?:Football|Rugby|Tennis|Handball|Basketball|Basket-ball"
               r"|Cyclisme|Formule\s*1|Boxe|MMA|Volley(?:ball|[\s-]ball)?|Golf"
               r"|Natation|Athlétisme|Ski|Voile|Équitation|Motocyclisme))"
               r"\s*[-–]\s*(?P<comp>.+)$", re.IGNORECASE),
]


def _guess_entity_type(name: str, sport: SportType) -> EntityType:
    """Guess whether a name is a club, country, player, or event."""
    name_lower = name.strip().lower()

    # Check nationality tag pattern: "N. Djokovic (SRB)"
    if PLAYER_WITH_NAT.search(name):
        return EntityType.PLAYER

    # Check if it's a known country (exact match only, not "Sporting Club Portugal")
    if name_lower in NATIONAL_TEAM_NAMES and len(name.split()) <= 2:
        return EntityType.COUNTRY

    # Individual sports → player
    if sport in (SportType.TENNIS, SportType.MMA, SportType.BOXE, SportType.GOLF):
        # If it looks like a person name (2+ words, starts with cap)
        words = name.strip().split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w not in ("de", "van", "von", "du")):
            return EntityType.PLAYER

    return EntityType.CLUB


def _parse_player_name(raw: str) -> tuple[str, Optional[str]]:
    """
    Parse player with optional nationality.
    "N. Djokovic (SRB)" → ("N. Djokovic", "rs")
    "Francis Ngannou (CMR)" → ("Francis Ngannou", "cm")
    "Carlos Alcaraz" → ("Carlos Alcaraz", None)
    """
    m = PLAYER_WITH_NAT.search(raw)
    if m:
        name = m.group("name").strip()
        nat_code = m.group("nat").lower()
        country = ISO3_TO_ISO2.get(nat_code, nat_code[:2].lower())
        return name, country
    return raw.strip(), None


def _build_entity(raw_name: str, sport: SportType) -> Entity:
    """Build a structured Entity from a raw name string."""
    raw_name = raw_name.strip()
    entity_type = _guess_entity_type(raw_name, sport)

    if entity_type == EntityType.PLAYER:
        clean_name, country_code = _parse_player_name(raw_name)
        return Entity(
            name=clean_name,
            type=EntityType.PLAYER,
            country_code=country_code,
        )

    if entity_type == EntityType.COUNTRY:
        name_lower = raw_name.lower()
        country_code = COUNTRY_CODES.get(name_lower)
        return Entity(
            name=raw_name,
            type=EntityType.COUNTRY,
            country_code=country_code,
        )

    # Club
    return Entity(
        name=raw_name,
        type=EntityType.CLUB,
    )


def extract_competition(prog: dict) -> Optional[str]:
    """Extract competition name from XMLTV title or subtitle."""
    title = prog.get("title", "")
    subtitle = (prog.get("subtitle") or "").strip()

    def _clean(comp: str) -> str:
        comp = re.sub(r",?\s*(\d+)e\s*journée", r" · J\1", comp)
        comp = re.sub(r",?\s*(\d+)e\s*étape", r" · Étape \1", comp)
        return comp.strip()

    # Standard "Sport : Competition" format
    for pattern in TITLE_COMP_PATTERNS:
        m = pattern.match(title)
        if m:
            comp = m.group("comp").strip()
            # Strip embedded matchup like "Ligue 1 | PSG / OM" → keep "Ligue 1"
            comp = re.split(r"\s*[|]\s*", comp)[0]
            return _clean(comp)

    # Bare matchup title (e.g. "Fribourg / Bayern Munich") →
    # try to extract competition from subtitle: "Bundesliga - 28e journée"
    _BARE_MATCHUP = re.compile(r"^[^:/|]+\s*/\s*[^:/|]+$")
    if _BARE_MATCHUP.match(title.strip()) and subtitle:
        # Subtitle format: "Competition - round" or "Competition. round."
        sub_clean = re.split(r"\s*[-–]\s*\d", subtitle)[0]  # strip round number
        sub_clean = re.split(r"\.\s*\d", sub_clean)[0]
        sub_clean = sub_clean.rstrip(" .-–")
        if sub_clean and len(sub_clean) > 2:
            return _clean(sub_clean)

    return None


def extract_matchup(prog: dict, sport: SportType) -> tuple[Optional[Entity], Optional[Entity]]:
    """Extract team1 and team2 from title or subtitle."""
    title = prog.get("title") or ""
    subtitle = prog.get("subtitle") or ""

    # Solo-event sports: stages, races, courses — not matchups
    SOLO_SPORTS = {SportType.F1, SportType.CYCLISME, SportType.MOTOGP, SportType.SKI, SportType.GOLF, SportType.VOILE}
    if sport in SOLO_SPORTS:
        return None, None

    def _clean_team(raw: str) -> str:
        """Strip trailing competition/round info from a team name."""
        # "Real Madrid. Euroligue masculine. 36e journée." → "Real Madrid"
        raw = re.split(r"\.\s*[A-Z]", raw)[0]
        # "Sporting CP. Champions League." → "Sporting CP"
        raw = re.split(r",\s*\d", raw)[0]
        return raw.strip(" .,")

    # ── Priority: if title is a bare matchup "Team1 / Team2", use it directly ──
    # e.g. "Fribourg / Bayern Munich", "Real Madrid / Bayern Munich"
    _BARE_MATCHUP = re.compile(
        r"^(?P<t1>[A-ZÀ-Üa-zà-ü0-9][^:/|]+?)\s*/\s*(?P<t2>[A-ZÀ-Üa-zà-ü0-9][^:/|]+)$"
    )
    m = _BARE_MATCHUP.match(title.strip())
    if m:
        t1 = _build_entity(_clean_team(m.group("t1")), sport)
        t2 = _build_entity(_clean_team(m.group("t2")), sport)
        return t1, t2

    # ── Also check: "Sport : Competition | Team1 / Team2" in title ──
    _PIPE_MATCHUP = re.compile(r"\|\s*(?P<t1>.+?)\s*/\s*(?P<t2>.+)$")
    m = _PIPE_MATCHUP.search(title)
    if m:
        t1 = _build_entity(_clean_team(m.group("t1")), sport)
        t2 = _build_entity(_clean_team(m.group("t2")), sport)
        return t1, t2

    cleaned = subtitle.strip()

    # Remove round/match labels like "Finale messieurs : ", "1/4 de finale : "
    cleaned = re.sub(
        r"^(?:finale|demi-finale|quart\s+de\s+finale|1\/\d+(?:\s*de\s+finale)?"
        r"|match|huitièmes?\s+de\s+finale|seizièmes?\s+de\s+finale"
        r"|phase\s+de\s+(?:poules?|groupes?)"
        r"|qualifications?|préliminaires?|barrages?)"
        r"(?:\s+(?:messieurs|dames|femmes|hommes|mixte|aller|retour))?\s*[:–-]\s*",
        "", cleaned, flags=re.IGNORECASE,
    ).strip()

    # Try to find teams via " / " separator (most reliable)
    if " / " in cleaned:
        parts = cleaned.split(" / ", 1)
        left = parts[0].strip()
        right = parts[1].strip()

        # If left side has " - ", the prefix is competition context
        # e.g. "Match Amical - Colombie" → take "Colombie"
        # But beware of team names with " - " (rare in French context)
        if " - " in left:
            # Check if right part of left looks like a team/country
            left_parts = left.rsplit(" - ", 1)
            candidate = left_parts[-1].strip()
            # If candidate is a known country or looks like a team name, use it
            if (candidate.lower() in COUNTRY_CODES
                or candidate.lower() in NATIONAL_TEAM_NAMES
                or len(candidate.split()) <= 4):
                left = candidate

        t1 = _build_entity(_clean_team(left), sport)
        t2 = _build_entity(_clean_team(right), sport)
        return t1, t2

    # Try other separators: " vs ", " contre "
    for sep in [" vs. ", " vs ", " contre "]:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)
            if len(parts) == 2:
                t1 = _build_entity(parts[0].strip(), sport)
                t2 = _build_entity(parts[1].strip(), sport)
                return t1, t2

    # Try " - " as team separator ONLY if both sides look like teams
    if " - " in cleaned:
        parts = cleaned.split(" - ")
        if len(parts) == 2:
            left, right = parts[0].strip(), parts[1].strip()
            # Both sides should be short (team names, not descriptions)
            if len(left.split()) <= 5 and len(right.split()) <= 5:
                t1 = _build_entity(left, sport)
                t2 = _build_entity(right, sport)
                return t1, t2

    # ── Fix 3: Fallback to description ──
    # If subtitle didn't yield teams, try to find "Equipe1 / Equipe2" in desc
    desc = prog.get("description") or ""
    desc_match = re.search(
        r"(?:entre\s+(?:l[ea']\s*)?|opposant\s+)"
        r"(?P<t1>[A-ZÀ-Ü][A-Za-zÀ-ü\s'-]+?)"
        r"\s+(?:et|face à|contre)\s+(?:l[ea']\s*)?"
        r"(?P<t2>[A-ZÀ-Ü][A-Za-zÀ-ü\s'-]+?)(?:\s+(?:au|à|sur|dans|pour))",
        desc,
    )
    if desc_match:
        t1 = _build_entity(desc_match.group("t1").strip(), sport)
        t2 = _build_entity(desc_match.group("t2").strip(), sport)
        return t1, t2

    # No matchup found
    return None, None


# ═══════════════════════════════════════════════════════
# CHANNEL NORMALIZATION
# ═══════════════════════════════════════════════════════

# Known channel slug mappings
CHANNEL_SLUG_MAP = {
    # TNT Gratuite
    "france 2": ("france-2", True),
    "france 3": ("france-3", True),
    "france 4": ("france-4", True),
    "france 5": ("france-5", True),
    "tf1": ("tf1", True),
    "m6": ("m6", True),
    "l'equipe": ("lequipe", True),
    "l'équipe": ("lequipe", True),
    "sport en france": ("sport-en-france", True),

    # Canal+
    "canal+": ("canal-plus", False),
    "canal+ sport": ("canal-plus-sport", False),
    "canal+ foot": ("canal-plus-foot", False),
    "canal+ sport 1": ("canal-plus-sport", False),
    "canal+ sport 2": ("canal-plus-sport-2", False),
    "canal+ sport 3": ("canal-plus-sport-3", False),
    "canal+ sport 4": ("canal-plus-sport-4", False),
    "canal+ sport 5": ("canal-plus-sport-5", False),
    "canal+ live 1": ("canal-plus", False),
    "canal+ live 2": ("canal-plus", False),
    "canal+ live 3": ("canal-plus", False),
    "canal+ live 4": ("canal-plus", False),
    "canal+ uhd": ("canal-plus", False),
    "canal+ premier league": ("canal-plus-sport", False),
    "infosport+": ("infosport-plus", False),

    # beIN Sports
    "bein sports 1": ("bein-1", False),
    "bein sports 2": ("bein-2", False),
    "bein sports 3": ("bein-3", False),
    "bein sports max 1": ("bein-1", False),
    "bein sports max 2": ("bein-2", False),
    "bein sports max 3": ("bein-3", False),
    "bein sports max 4": ("bein-3", False),
    "bein sports max 5": ("bein-3", False),
    "bein sports max 6": ("bein-3", False),

    # RMC Sport
    "rmc sport 1": ("rmc-sport-1", False),
    "rmc sport 2": ("rmc-sport-2", False),

    # Eurosport
    "eurosport 1": ("eurosport-1", False),
    "eurosport 2": ("eurosport-2", False),

    # DAZN
    "dazn 1": ("dazn-1", False),
    "dazn 2": ("dazn-2", False),

    # Amazon Prime Video
    "prime video": ("prime-video", False),
    "amazon prime video": ("prime-video", False),
}


def build_channel(raw_channel: dict) -> Channel:
    """Normalize an XMLTV channel dict into a Channel model."""
    name = raw_channel.get("name", "")
    name_lower = name.lower().strip()

    slug, is_free = CHANNEL_SLUG_MAP.get(name_lower, (
        re.sub(r"[^a-z0-9]+", "-", name_lower).strip("-"),
        False,
    ))

    return Channel(
        id=raw_channel.get("id", ""),
        name=name,
        icon_url=raw_channel.get("icon_url"),
        slug=slug,
        is_free=is_free,
    )


# ═══════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════

def _make_event_id(prog: dict) -> str:
    """Generate a stable unique ID from programme data."""
    key = f"{prog['channel_id']}_{prog['start'].isoformat()}_{prog.get('title', '')}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def _compute_status(start: datetime, end: Optional[datetime]) -> EventStatus:
    """Determine if event is upcoming, live, or finished."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    if end and now > end:
        return EventStatus.FINISHED
    if now >= start:
        return EventStatus.LIVE
    return EventStatus.UPCOMING


def extract_sport_events(
    programmes: list[dict],
    channels: dict[str, dict],
) -> list[SportEvent]:
    """
    Main pipeline: raw XMLTV programmes → list of SportEvent.

    1. Filter sport programmes
    2. Classify sport type
    3. Extract competition + teams
    4. Enrich entities with logos/photos from registry
    5. Build normalized SportEvent objects
    """
    # Import entity enrichment (lazy to avoid circular imports)
    try:
        from .entity_registry import enrich_entity
        has_registry = True
    except ImportError:
        has_registry = False

    events = []
    sport_count = 0
    skipped = 0
    enriched_count = 0

    for prog in programmes:
        if not is_sport_programme(prog):
            skipped += 1
            continue

        if not is_actual_match(prog):
            skipped += 1
            continue

        sport_count += 1
        sport = classify_sport(prog)

        # Build channel
        ch_data = channels.get(prog["channel_id"], {"id": prog["channel_id"], "name": "?"})
        channel = build_channel(ch_data)

        # Extract competition
        competition = extract_competition(prog)

        # Extract matchup
        team1, team2 = extract_matchup(prog, sport)

        # ── Step 4: Enrich entities ──
        if has_registry and (team1 or team2):
            sport_str = sport.value if hasattr(sport, 'value') else str(sport)
            if team1:
                enriched = enrich_entity(team1.model_dump(), sport_str)
                if enriched.get("logo_url") or enriched.get("photo_url"):
                    enriched_count += 1
                team1 = Entity(**{k: v for k, v in enriched.items()
                                  if k in Entity.model_fields})
            if team2:
                enriched = enrich_entity(team2.model_dump(), sport_str)
                if enriched.get("logo_url") or enriched.get("photo_url"):
                    enriched_count += 1
                team2 = Entity(**{k: v for k, v in enriched.items()
                                  if k in Entity.model_fields})

        # Build event
        event = SportEvent(
            id=_make_event_id(prog),
            sport=sport,
            competition=competition,
            title=prog.get("title", ""),
            subtitle=prog.get("subtitle"),
            description=prog.get("description"),
            team1=team1,
            team2=team2,
            channel=channel,
            start=prog["start"],
            end=prog["end"],
            status=_compute_status(prog["start"], prog.get("end")),
        )
        events.append(event)

    logger.info(
        f"Extraction complete: {sport_count} sport / {skipped} non-sport → "
        f"{len(events)} events ({enriched_count} entities enriched with visuals)"
    )

    # ── Deduplicate: same match on multiple channels → keep one ──
    # Priority order: known French channels > others
    PRIORITY_SLUGS = {
        "tf1": 0, "france-2": 1, "france-3": 2, "m6": 3,
        "canal-plus": 10, "canal-plus-sport": 11, "canal-plus-foot": 12,
        "bein-1": 20, "bein-2": 21, "bein-3": 22,
        "rmc-sport-1": 30, "rmc-sport-2": 31,
        "eurosport-1": 40, "eurosport-2": 41,
        "dazn-1": 50, "dazn-2": 51,
        "prime-video": 60, "lequipe": 70, "sport-en-france": 80,
    }

    def _dedup_key(e: SportEvent) -> str:
        """Key to identify the same match regardless of channel."""
        # Normalize title: lowercase, remove punctuation
        title = re.sub(r"[^\w\s]", "", e.title.lower()).strip()
        start = e.start.strftime("%Y-%m-%dT%H:%M") if e.start else ""
        return f"{title}_{start}"

    seen: dict[str, SportEvent] = {}
    for event in events:
        key = _dedup_key(event)
        if key not in seen:
            seen[key] = event
        else:
            # Keep the event from the highest-priority (lowest score) channel
            existing_priority = PRIORITY_SLUGS.get(seen[key].channel.slug, 999)
            new_priority = PRIORITY_SLUGS.get(event.channel.slug, 999)
            if new_priority < existing_priority:
                seen[key] = event

    events = list(seen.values())

    # Sort: live first, then by start time
    events.sort(key=lambda e: (
        0 if e.status == EventStatus.LIVE else 1 if e.status == EventStatus.UPCOMING else 2,
        e.start,
    ))

    return events
