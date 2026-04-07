"""
SportZap — Standalone pipeline test (stdlib only)
Tests the core XMLTV parsing + sport extraction logic.
"""
import sys
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET


# ═══ INLINE PARSER (from xmltv_parser.py) ═══

def parse_xmltv_datetime(raw):
    raw = raw.strip()
    parts = raw.split()
    dt_str = parts[0]
    tz_str = parts[1] if len(parts) > 1 else "+0000"
    dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
    tz_sign = 1 if tz_str[0] == "+" else -1
    tz_hours = int(tz_str[1:3])
    tz_mins = int(tz_str[3:5])
    tz_offset = timedelta(hours=tz_hours * tz_sign, minutes=tz_mins * tz_sign)
    return dt.replace(tzinfo=timezone(tz_offset))


def parse_xmltv(path):
    root = ET.parse(path).getroot()
    
    # Channels
    channels = {}
    for ch in root.findall("channel"):
        cid = ch.get("id", "")
        name_el = ch.find("display-name")
        icon_el = ch.find("icon")
        channels[cid] = {
            "id": cid,
            "name": name_el.text.strip() if name_el is not None and name_el.text else cid,
            "icon_url": icon_el.get("src") if icon_el is not None else None,
        }
    
    # Programmes
    programmes = []
    for prog in root.findall("programme"):
        title_el = prog.find("title")
        if title_el is None or not title_el.text:
            continue
        
        sub_el = prog.find("sub-title")
        desc_el = prog.find("desc")
        categories = [c.text.strip().lower() for c in prog.findall("category") if c.text]
        
        programmes.append({
            "channel_id": prog.get("channel", ""),
            "start": parse_xmltv_datetime(prog.get("start", "")),
            "end": parse_xmltv_datetime(prog.get("stop", "")) if prog.get("stop") else None,
            "title": title_el.text.strip(),
            "subtitle": sub_el.text.strip() if sub_el is not None and sub_el.text else None,
            "description": desc_el.text.strip() if desc_el is not None and desc_el.text else None,
            "categories": categories,
        })
    
    return channels, programmes


# ═══ INLINE SPORT EXTRACTOR (from sport_extractor.py) ═══

SPORT_CATEGORIES = {
    "sport", "football", "rugby", "tennis", "basket", "basket-ball",
    "basketball", "handball", "hand-ball", "cyclisme", "formule 1",
    "sport mécanique", "sport mecanique", "athlétisme", "natation",
    "golf", "voile", "ski", "biathlon", "boxe", "mma",
    "sport de combat", "sports de combat", "volley", "volleyball",
    "hippisme", "équitation", "auto-moto", "motocyclisme", "motogp",
}

SPORT_TITLE_PATTERNS = [
    r"(?i)\b(?:ligue\s*[12]|liga|serie\s*a|bundesliga|premier\s*league)\b",
    r"(?i)\b(?:champions\s*league|europa\s*league)\b",
    r"(?i)\b(?:top\s*14|pro\s*d2|champions\s*cup)\b",
    r"(?i)\b(?:masters\s*1000|atp|wta|roland[\s-]*garros|wimbledon)\b",
    r"(?i)\b(?:grand\s*prix|formule\s*1|f1)\b",
    r"(?i)\b(?:nba|nfl|nhl)\b",
    r"(?i)\b(?:six\s*nations|golden\s*league|coupe\s*du\s*monde)\b",
    r"(?i)\b(?:ufc|pfl|bellator)\b",
    r"(?i)\b(?:tour\s+de)\b",
]

CATEGORY_SPORT_MAP = [
    (["football", "foot"], "football"),
    (["rugby"], "rugby"),
    (["tennis"], "tennis"),
    (["basket", "basketball", "basket-ball"], "basket"),
    (["formule 1", "f1", "sport mécanique", "sport mecanique"], "f1"),
    (["cyclisme", "vélo"], "cyclisme"),
    (["mma", "ufc", "pfl", "sport de combat", "arts martiaux"], "mma"),
    (["boxe"], "boxe"),
    (["handball", "hand-ball"], "handball"),
    (["natation"], "natation"),
    (["athlétisme", "athletisme"], "athletisme"),
    (["ski", "biathlon", "sport d'hiver"], "ski"),
    (["golf"], "golf"),
    (["voile"], "voile"),
    (["volley", "volleyball"], "volleyball"),
]

TITLE_CLASSIFY = [
    (r"(?i)\bfoot(?:ball)?\b", "football"),
    (r"(?i)\brugby\b", "rugby"),
    (r"(?i)\btennis\b", "tennis"),
    (r"(?i)\bbasket", "basket"),
    (r"(?i)\bnba\b", "basket"),
    (r"(?i)\b(?:formule\s*1|f1|grand\s*prix)\b", "f1"),
    (r"(?i)\b(?:cyclisme|tour\s+de|étape)\b", "cyclisme"),
    (r"(?i)\b(?:mma|ufc|pfl)\b", "mma"),
    (r"(?i)\bboxe\b", "boxe"),
    (r"(?i)\bhandball\b", "handball"),
    (r"(?i)\bvolley", "volleyball"),
]

COUNTRY_CODES = {
    "france": "fr", "danemark": "dk", "allemagne": "de", "espagne": "es",
    "italie": "it", "angleterre": "gb-eng", "galles": "gb-wls",
    "portugal": "pt", "belgique": "be", "brésil": "br", "argentine": "ar",
    "colombie": "co", "mexique": "mx", "uruguay": "uy", "pérou": "pe",
    "islande": "is",
    "srb": "rs", "esp": "es", "fra": "fr", "gbr": "gb", "cmr": "cm",
    "den": "dk", "ger": "de", "ita": "it", "bra": "br", "usa": "us",
    "jpn": "jp", "aus": "au", "ned": "nl", "por": "pt",
    "col": "co",
}

CHANNEL_SLUGS = {
    "france 2": ("france-2", True),
    "france 3": ("france-3", True),
    "tf1": ("tf1", True),
    "canal+": ("canal-plus", False),
    "bein sports 1": ("bein-1", False),
    "bein sports 2": ("bein-2", False),
    "rmc sport 1": ("rmc-sport-1", False),
    "eurosport 1": ("eurosport-1", False),
    "eurosport 2": ("eurosport-2", False),
    "l'equipe": ("lequipe", True),
    "l'équipe": ("lequipe", True),
    "dazn 1": ("dazn-1", False),
}

PLAYER_NAT_RE = re.compile(r"(?P<name>[A-ZÀ-Ü][.\s]?\s*[A-ZÀ-Üa-zà-ü'-]+(?:\s+[A-ZÀ-Üa-zà-ü'-]+)*)\s*\((?P<nat>[A-Z]{3})\)")
INDIVIDUAL_SPORTS = {"tennis", "mma", "boxe", "golf"}


def is_sport(prog):
    cats = set(prog.get("categories", []))
    if cats & SPORT_CATEGORIES:
        return True
    combined = prog.get("title", "") + " " + (prog.get("subtitle") or "")
    for p in SPORT_TITLE_PATTERNS:
        if re.search(p, combined):
            return True
    return False


def classify(prog):
    cats = prog.get("categories", [])
    combined = prog.get("title", "") + " " + (prog.get("subtitle") or "")
    for keywords, sport in CATEGORY_SPORT_MAP:
        for cat in cats:
            if any(kw in cat for kw in keywords):
                return sport
    for pattern, sport in TITLE_CLASSIFY:
        if re.search(pattern, combined):
            return sport
    return "other"


def extract_comp(title):
    # Pattern 1: "Sport : Competition"
    m = re.match(r"^(?P<sport>[^:]+?)\s*:\s*(?P<comp>.+)$", title)
    if m:
        comp = m.group("comp").strip()
        comp = re.sub(r",?\s*(\d+)e\s*journée", r" · J\1", comp)
        comp = re.sub(r",?\s*(\d+)e\s*étape", r" · Étape \1", comp)
        return comp
    # Pattern 2: "Sport - Competition" (TF1 format)
    m = re.match(
        r"^(?:Football|Rugby|Tennis|Handball|Basketball|Basket-ball"
        r"|Cyclisme|Formule\s*1|Boxe|MMA|Volley(?:ball)?|Golf"
        r"|Natation|Athlétisme|Ski|Voile|Équitation|Motocyclisme)"
        r"\s*[-–]\s*(?P<comp>.+)$", title, re.IGNORECASE
    )
    if m:
        comp = m.group("comp").strip()
        comp = re.sub(r",?\s*(\d+)e\s*journée", r" · J\1", comp)
        return comp
    return None


def entity_type(name, sport):
    if PLAYER_NAT_RE.search(name):
        return "player"
    if name.strip().lower() in COUNTRY_CODES:
        return "country"
    if sport in INDIVIDUAL_SPORTS:
        words = name.strip().split()
        if len(words) >= 2:
            return "player"
    return "club"


def parse_player(raw):
    m = PLAYER_NAT_RE.search(raw)
    if m:
        name = m.group("name").strip()
        nat = m.group("nat").lower()
        cc = COUNTRY_CODES.get(nat, nat[:2])
        return name, cc
    return raw.strip(), None


def build_entity(raw, sport):
    raw = raw.strip()
    etype = entity_type(raw, sport)
    if etype == "player":
        name, cc = parse_player(raw)
        return {"name": name, "type": "player", "country_code": cc}
    if etype == "country":
        cc = COUNTRY_CODES.get(raw.lower())
        return {"name": raw, "type": "country", "country_code": cc}
    return {"name": raw, "type": "club", "country_code": None}


def extract_teams(subtitle, sport, desc=None):
    if not subtitle and not desc:
        return None, None
    # Solo-event sports don't have matchups
    if sport in ("f1", "cyclisme", "motogp", "ski", "golf", "voile"):
        return None, None

    cleaned = (subtitle or "").strip()

    # Strip round/match prefixes: "Quart de finale retour - ", "Match Amical - " etc.
    cleaned = re.sub(
        r"^(?:finale|demi-finale|quart\s+de\s+finale|1\/\d+(?:\s*de\s+finale)?"
        r"|match(?:\s+amical)?|huitièmes?\s+de\s+finale|seizièmes?\s+de\s+finale"
        r"|phase\s+de\s+(?:poules?|groupes?)"
        r"|qualifications?|préliminaires?|barrages?)"
        r"(?:\s+(?:messieurs|dames|femmes|hommes|mixte|aller|retour))?\s*[:–-]\s*",
        "", cleaned, flags=re.IGNORECASE
    ).strip()

    # Try " / " first (most common)
    if " / " in cleaned:
        parts = cleaned.split(" / ", 1)
        left, right = parts[0].strip(), parts[1].strip()
        # Strip competition prefix from left: "Match Amical - Colombie" → "Colombie"
        if " - " in left:
            left_parts = left.rsplit(" - ", 1)
            candidate = left_parts[-1].strip()
            if candidate.lower() in COUNTRY_CODES or len(candidate.split()) <= 4:
                left = candidate
        return build_entity(left, sport), build_entity(right, sport)

    # Try " vs "
    for sep in [" vs. ", " vs ", " contre "]:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)
            if len(parts) == 2:
                return build_entity(parts[0].strip(), sport), build_entity(parts[1].strip(), sport)

    # Try " - " only if both sides look like team names
    if " - " in cleaned:
        parts = cleaned.split(" - ")
        if len(parts) == 2:
            left, right = parts[0].strip(), parts[1].strip()
            if len(left.split()) <= 5 and len(right.split()) <= 5:
                return build_entity(left, sport), build_entity(right, sport)

    # Fallback: try to find teams in description
    if desc:
        desc_match = re.search(
            r"(?:entre\s+(?:l[ea']\s*)?|opposant\s+)"
            r"(?P<t1>[A-ZÀ-Ü][A-Za-zÀ-ü\s'-]+?)"
            r"\s+(?:et|face à|contre)\s+(?:l[ea']\s*)?"
            r"(?P<t2>[A-ZÀ-Ü][A-Za-zÀ-ü\s'-]+?)(?:\s+(?:au|à|sur|dans|pour))",
            desc,
        )
        if desc_match:
            return build_entity(desc_match.group("t1").strip(), sport), build_entity(desc_match.group("t2").strip(), sport)

    return None, None


def build_channel(raw_ch):
    name = raw_ch.get("name", "")
    slug, free = CHANNEL_SLUGS.get(name.lower().strip(), (
        re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), False
    ))
    return {"id": raw_ch["id"], "name": name, "slug": slug, "is_free": free}


def pipeline(programmes, channels):
    events = []
    for prog in programmes:
        if not is_sport(prog):
            continue
        sport = classify(prog)
        comp = extract_comp(prog.get("title", ""))
        t1, t2 = extract_teams(prog.get("subtitle"), sport, desc=prog.get("description"))
        ch = build_channel(channels.get(prog["channel_id"], {"id": prog["channel_id"], "name": "?"}))
        
        key = f"{prog['channel_id']}_{prog['start'].isoformat()}_{prog['title']}"
        eid = hashlib.md5(key.encode()).hexdigest()[:12]
        
        events.append({
            "id": eid,
            "sport": sport,
            "competition": comp,
            "title": prog["title"],
            "subtitle": prog.get("subtitle"),
            "team1": t1,
            "team2": t2,
            "channel": ch,
            "start": prog["start"].isoformat(),
            "end": prog["end"].isoformat() if prog.get("end") else None,
        })
    
    events.sort(key=lambda e: e["start"])
    return events


# ═══ RUN ═══

def main():
    sample = Path(__file__).parent.parent / "data" / "sample_xmltv.xml"
    assert sample.exists(), f"Not found: {sample}"
    
    print("=" * 64)
    print("  SPORTZAP — PIPELINE TEST")
    print("=" * 64)
    
    # Parse
    channels, programmes = parse_xmltv(sample)
    print(f"\n  📡 Channels parsed:    {len(channels)}")
    print(f"  📄 Programmes parsed:  {len(programmes)}")
    
    # Filter
    sport_progs = [p for p in programmes if is_sport(p)]
    non_sport = [p for p in programmes if not is_sport(p)]
    print(f"\n  ⚽ Sport programmes:   {len(sport_progs)}")
    print(f"  ❌ Non-sport excluded: {len(non_sport)}")
    for ns in non_sport:
        print(f"     ✗ {ns['title']}")
    
    # Extract
    events = pipeline(programmes, channels)
    print(f"\n  🎯 Events extracted:   {len(events)}")
    
    # Display
    print(f"\n{'━' * 64}")
    errors = []
    
    for i, ev in enumerate(events, 1):
        sport_colors = {
            "football": "⚽", "rugby": "🏉", "tennis": "🎾", "basket": "🏀",
            "f1": "🏎️ ", "cyclisme": "🚴", "mma": "🥊", "handball": "🤾",
        }
        icon = sport_colors.get(ev["sport"], "🏅")
        
        print(f"\n  {i:2d}. {icon} {ev['sport'].upper():12s} │ {ev['competition'] or '—'}")
        
        if ev["team1"] and ev["team2"]:
            t1 = ev["team1"]
            t2 = ev["team2"]
            t1_str = f"{t1['name']} [{t1['type']}"
            if t1.get("country_code"): t1_str += f":{t1['country_code']}"
            t1_str += "]"
            t2_str = f"{t2['name']} [{t2['type']}"
            if t2.get("country_code"): t2_str += f":{t2['country_code']}"
            t2_str += "]"
            print(f"      ┃ {t1_str}  vs  {t2_str}")
        elif ev["team1"]:
            t1 = ev["team1"]
            print(f"      ┃ {t1['name']} [{t1['type']}]")
        
        ch = ev["channel"]
        free_tag = "🆓 FREE" if ch["is_free"] else "💰 PAID"
        start_time = ev["start"].split("T")[1][:5]
        print(f"      ┃ {ch['name']} ({ch['slug']}) {free_tag} │ {start_time}")
    
    # ── Validations ──
    print(f"\n{'━' * 64}")
    print(f"  VALIDATIONS")
    print(f"{'━' * 64}")
    
    # 1. Correct filtering
    expected_sport_count = 15  # 11 original + 4 new edge cases
    if len(events) != expected_sport_count:
        errors.append(f"Expected {expected_sport_count} sport events, got {len(events)}")
    if len(non_sport) != 3:
        errors.append(f"Expected 3 non-sport excluded, got {len(non_sport)}")
    
    # 2. Sport classification
    sports_found = {e["sport"] for e in events}
    expected_sports = {"football", "rugby", "tennis", "basket", "f1", "cyclisme", "mma", "handball"}
    missing = expected_sports - sports_found
    if missing:
        errors.append(f"Missing sport types: {missing}")
    
    # 3. Entity extraction quality
    # PSG vs OM — both clubs
    psg = next((e for e in events if e["subtitle"] and "Paris" in e["subtitle"]), None)
    if psg:
        if not psg["team1"]:
            errors.append("PSG match: team1 not extracted")
        elif psg["team1"]["type"] != "club":
            errors.append(f"PSG should be 'club', got '{psg['team1']['type']}'")
    
    # Djokovic — player with country rs
    djoko = next((e for e in events if e["subtitle"] and "Djokovic" in e["subtitle"]), None)
    if djoko:
        if not djoko["team1"]:
            errors.append("Djokovic: team1 not extracted")
        else:
            if djoko["team1"]["type"] != "player":
                errors.append(f"Djokovic should be 'player', got '{djoko['team1']['type']}'")
            if djoko["team1"]["country_code"] != "rs":
                errors.append(f"Djokovic country should be 'rs', got '{djoko['team1'].get('country_code')}'")
    
    # France vs Danemark — both countries
    france = next((e for e in events if e["subtitle"] and "France / Danemark" in (e["subtitle"] or "")), None)
    if france:
        if not france["team1"]:
            errors.append("France: team1 not extracted")
        else:
            if france["team1"]["type"] != "country":
                errors.append(f"France should be 'country', got '{france['team1']['type']}'")
            if france["team1"]["country_code"] != "fr":
                errors.append(f"France code should be 'fr', got '{france['team1'].get('country_code')}'")
        if france["team2"] and france["team2"]["type"] != "country":
            errors.append(f"Danemark should be 'country', got '{france['team2']['type']}'")
    
    # Ngannou vs Fury — both players
    mma = next((e for e in events if e["sport"] == "mma"), None)
    if mma:
        if not mma["team1"]:
            errors.append("MMA: team1 not extracted")
        elif mma["team1"]["type"] != "player":
            errors.append(f"Ngannou should be 'player', got '{mma['team1']['type']}'")
    
    # 4. Channel normalization
    dazn_events = [e for e in events if e["channel"]["slug"] == "dazn-1"]
    canal_events = [e for e in events if e["channel"]["slug"] == "canal-plus"]
    free_events = [e for e in events if e["channel"]["is_free"]]

    if len(dazn_events) < 2:
        errors.append(f"Expected ≥2 DAZN events, got {len(dazn_events)}")
    if len(canal_events) < 2:
        errors.append(f"Expected ≥2 Canal+ events, got {len(canal_events)}")
    if len(free_events) < 1:
        errors.append(f"Expected ≥1 free channel events, got {len(free_events)}")

    # 5. NEW EDGE CASES

    # 5a. TF1 format: "Football - Match Amical" + "Match Amical - Colombie / France"
    colombie_match = next((e for e in events if e["subtitle"] and "Colombie" in (e["subtitle"] or "")), None)
    if colombie_match:
        if colombie_match["competition"] != "Match Amical":
            errors.append(f"Colombie match comp should be 'Match Amical', got '{colombie_match['competition']}'")
        if not colombie_match["team1"]:
            errors.append("Colombie match: team1 not extracted")
        elif colombie_match["team1"]["name"] != "Colombie":
            errors.append(f"Team1 should be 'Colombie', got '{colombie_match['team1']['name']}'")
        if colombie_match["team1"] and colombie_match["team1"]["type"] != "country":
            errors.append(f"Colombie should be 'country', got '{colombie_match['team1']['type']}'")
        if not colombie_match["team2"]:
            errors.append("Colombie match: team2 not extracted")
        elif colombie_match["team2"]["type"] != "country":
            errors.append(f"France (in Colombie match) should be 'country', got '{colombie_match['team2']['type']}'")
    else:
        errors.append("Colombie / France match not found at all")

    # 5b. Minimal format: "Football" + "Monaco - Lens"
    monaco_match = next((e for e in events if e["subtitle"] and "Monaco" in (e["subtitle"] or "")), None)
    if monaco_match:
        if not monaco_match["team1"]:
            errors.append("Monaco match: team1 not extracted from ' - ' separator")
        elif monaco_match["team1"]["name"] != "Monaco":
            errors.append(f"Expected 'Monaco', got '{monaco_match['team1']['name']}'")
    else:
        errors.append("Monaco - Lens match not found")

    # 5c. CL with prefix: "Quart de finale retour - Arsenal FC / Real Madrid"
    cl_match = next((e for e in events if e["subtitle"] and "Arsenal" in (e["subtitle"] or "")), None)
    if cl_match:
        if not cl_match["team1"]:
            errors.append("CL match: team1 not extracted (prefix not stripped)")
        elif "Arsenal" not in cl_match["team1"]["name"]:
            errors.append(f"CL team1 should contain 'Arsenal', got '{cl_match['team1']['name']}'")
    else:
        errors.append("Arsenal / Real Madrid CL match not found")

    # 5d. Desc fallback: no subtitle, "entre le PSG et Lyon" in desc
    coupe_match = next((e for e in events if e["title"] and "Coupe de France" in e["title"]), None)
    if coupe_match:
        if not coupe_match["team1"]:
            errors.append("Coupe de France: team extraction from desc failed")
        else:
            if "PSG" not in coupe_match["team1"]["name"]:
                errors.append(f"Coupe de France team1 should contain 'PSG', got '{coupe_match['team1']['name']}'")
    else:
        errors.append("Coupe de France match not found")
    
    # ── Results ──
    if errors:
        print(f"\n  ❌ {len(errors)} FAILED:")
        for e in errors:
            print(f"     • {e}")
    else:
        print(f"\n  ✅ ALL PASSED")
    
    # Stats
    entity_types = set()
    for e in events:
        if e["team1"]: entity_types.add(e["team1"]["type"])
        if e["team2"]: entity_types.add(e["team2"]["type"])
    
    print(f"\n  Sports:       {', '.join(sorted(sports_found))}")
    print(f"  Entity types: {', '.join(sorted(entity_types))}")
    print(f"  Free/Paid:    {len(free_events)}/{len(events) - len(free_events)}")
    
    # JSON sample
    print(f"\n{'━' * 64}")
    print(f"  SAMPLE JSON (1st event)")
    print(f"{'━' * 64}")
    print(json.dumps(events[0], indent=2, ensure_ascii=False, default=str))
    
    return len(errors) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
