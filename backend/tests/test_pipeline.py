"""
SportZap — Pipeline test

Runs the full XMLTV → JSON pipeline on sample data
and validates extraction quality.
"""
import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.xmltv_parser import parse_xmltv
from app.sport_extractor import extract_sport_events, is_sport_programme, classify_sport


def main():
    sample = Path(__file__).parent.parent / "data" / "sample_xmltv.xml"
    assert sample.exists(), f"Sample file not found: {sample}"

    print("=" * 60)
    print("  SportZap Pipeline Test")
    print("=" * 60)

    # ── Step 1: Parse XMLTV ──
    print("\n▸ Step 1: Parsing XMLTV...")
    channels, programmes = parse_xmltv(sample)
    print(f"  Channels:    {len(channels)}")
    print(f"  Programmes:  {len(programmes)}")

    # ── Step 2: Filter sport ──
    sport_progs = [p for p in programmes if is_sport_programme(p)]
    non_sport = [p for p in programmes if not is_sport_programme(p)]
    print(f"\n▸ Step 2: Sport filter")
    print(f"  Sport:       {len(sport_progs)}")
    print(f"  Non-sport:   {len(non_sport)}")
    for ns in non_sport:
        print(f"    ✗ Excluded: {ns['title']}")

    # ── Step 3: Extract events ──
    print(f"\n▸ Step 3: Extraction pipeline")
    events = extract_sport_events(programmes, channels)
    print(f"  Events extracted: {len(events)}")

    # ── Step 4: Display results ──
    print(f"\n{'─' * 60}")
    print(f"  EXTRACTED SPORT EVENTS")
    print(f"{'─' * 60}")

    for i, ev in enumerate(events, 1):
        status_icon = {"live": "🔴", "upcoming": "⏳", "finished": "✅"}.get(ev.status.value, "?")

        print(f"\n  {i}. {status_icon} [{ev.sport.value.upper()}] {ev.competition or '—'}")
        print(f"     Title:   {ev.title}")

        if ev.team1 and ev.team2:
            t1 = f"{ev.team1.name} ({ev.team1.type.value}"
            if ev.team1.country_code:
                t1 += f", {ev.team1.country_code}"
            t1 += ")"
            t2 = f"{ev.team2.name} ({ev.team2.type.value}"
            if ev.team2.country_code:
                t2 += f", {ev.team2.country_code}"
            t2 += ")"
            print(f"     Match:   {t1}  vs  {t2}")
        elif ev.team1:
            print(f"     Entity:  {ev.team1.name} ({ev.team1.type.value})")
        elif ev.subtitle:
            print(f"     Detail:  {ev.subtitle}")

        print(f"     Channel: {ev.channel.name} [{ev.channel.slug}] {'🆓' if ev.channel.is_free else '💰'}")
        print(f"     Time:    {ev.start.strftime('%H:%M')} → {ev.end.strftime('%H:%M') if ev.end else '?'}")

    # ── Step 5: JSON output sample ──
    print(f"\n{'─' * 60}")
    print(f"  SAMPLE JSON OUTPUT (first event)")
    print(f"{'─' * 60}")
    if events:
        sample_json = events[0].model_dump(mode="json")
        print(json.dumps(sample_json, indent=2, ensure_ascii=False))

    # ── Step 6: Validation ──
    print(f"\n{'─' * 60}")
    print(f"  VALIDATION")
    print(f"{'─' * 60}")

    errors = []

    # Check all sport programmes were captured
    if len(events) != len(sport_progs):
        errors.append(f"Event count mismatch: {len(events)} events vs {len(sport_progs)} sport programmes")

    # Check non-sport was excluded
    excluded_titles = {"Journal de 20 heures", "Les Enfoirés 2026", "Les Carnets de Julie"}
    event_titles = {e.title for e in events}
    for title in excluded_titles:
        if title in event_titles:
            errors.append(f"Non-sport programme leaked through: {title}")

    # Check entity extraction
    events_with_teams = [e for e in events if e.team1]
    events_needing_teams = [e for e in events if e.subtitle and ("/" in e.subtitle or "vs" in e.subtitle.lower())]
    if len(events_with_teams) < len(events_needing_teams):
        errors.append(f"Missing team extraction: {len(events_with_teams)}/{len(events_needing_teams)} matchups parsed")

    # Check specific extractions
    psg_match = next((e for e in events if e.team1 and "Paris" in e.team1.name), None)
    if psg_match:
        if psg_match.team1.type.value != "club":
            errors.append(f"PSG should be type 'club', got '{psg_match.team1.type.value}'")
    else:
        # Check by subtitle
        psg_match = next((e for e in events if e.subtitle and "Paris" in e.subtitle), None)
        if psg_match:
            errors.append("PSG match found but team1 not extracted")

    djoko_match = next((e for e in events if e.team1 and "Djokovic" in e.team1.name), None)
    if djoko_match:
        if djoko_match.team1.type.value != "player":
            errors.append(f"Djokovic should be type 'player', got '{djoko_match.team1.type.value}'")
        if djoko_match.team1.country_code != "rs":
            errors.append(f"Djokovic country should be 'rs', got '{djoko_match.team1.country_code}'")

    france_match = next((e for e in events if e.team1 and e.team1.name == "France"), None)
    if france_match:
        if france_match.team1.type.value != "country":
            errors.append(f"France should be type 'country', got '{france_match.team1.type.value}'")
        if france_match.team1.country_code != "fr":
            errors.append(f"France country code should be 'fr', got '{france_match.team1.country_code}'")

    if errors:
        print(f"\n  ❌ {len(errors)} validation error(s):")
        for err in errors:
            print(f"    • {err}")
    else:
        print(f"\n  ✅ All validations passed!")

    # Stats summary
    sport_types_found = {e.sport.value for e in events}
    entity_types_found = set()
    for e in events:
        if e.team1:
            entity_types_found.add(e.team1.type.value)
        if e.team2:
            entity_types_found.add(e.team2.type.value)

    print(f"\n  Sports found:  {', '.join(sorted(sport_types_found))}")
    print(f"  Entity types:  {', '.join(sorted(entity_types_found))}")
    print(f"  Free channels: {sum(1 for e in events if e.channel.is_free)}/{len(events)}")

    return len(errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
