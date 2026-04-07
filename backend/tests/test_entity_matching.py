"""
Test entity registry matching against real XMLTV name variants.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.entity_registry import match_entity, enrich_entity, get_registry_stats


def main():
    print("=" * 64)
    print("  SPORTZAP — ENTITY MATCHING TEST")
    print("=" * 64)

    stats = get_registry_stats()
    print(f"\n  Registry: {stats['total_entities']} entities, {stats['total_aliases']} aliases")
    print(f"  By type:  {stats['by_type']}")
    print(f"  By sport: {stats['by_sport']}")

    errors = []

    # ── Test cases: (raw_name, sport, expected_short, expected_type) ──
    test_cases = [
        # Ligue 1 — real XMLTV variants
        ("Paris-SG", "football", "PSG", "club"),
        ("Paris SG", "football", "PSG", "club"),
        ("Olympique de Marseille", "football", "OM", "club"),
        ("Olympique Lyonnais", "football", "OL", "club"),
        ("LOSC Lille", "football", "LOSC", "club"),
        ("Monaco", "football", "Monaco", "club"),
        ("Lens", "football", "Lens", "club"),
        ("RC Lens", "football", "Lens", "club"),
        ("Saint-Étienne", "football", "ASSE", "club"),
        ("AS Saint-Etienne", "football", "ASSE", "club"),
        ("Stade Brestois", "football", "Brest", "club"),

        # Premier League
        ("Arsenal FC", "football", "Arsenal", "club"),
        ("Arsenal", "football", "Arsenal", "club"),
        ("Manchester City", "football", "Man City", "club"),
        ("Man City", "football", "Man City", "club"),
        ("Liverpool FC", "football", "Liverpool", "club"),
        ("Chelsea FC", "football", "Chelsea", "club"),
        ("Manchester United", "football", "Man Utd", "club"),

        # Liga
        ("Real Madrid", "football", "Real Madrid", "club"),
        ("FC Barcelone", "football", "Barça", "club"),
        ("Barcelone", "football", "Barça", "club"),
        ("Atlético Madrid", "football", "Atlético", "club"),

        # Serie A
        ("Juventus", "football", "Juventus", "club"),
        ("AC Milan", "football", "AC Milan", "club"),
        ("Inter Milan", "football", "Inter", "club"),
        ("SSC Napoli", "football", "Napoli", "club"),
        ("Naples", "football", "Napoli", "club"),

        # Bundesliga
        ("Bayern Munich", "football", "Bayern", "club"),
        ("Borussia Dortmund", "football", "BVB", "club"),

        # Top 14 rugby
        ("Stade Toulousain", "rugby", "Toulouse", "club"),
        ("Racing 92", "rugby", "Racing 92", "club"),
        ("Stade Français", "rugby", "Stade Français", "club"),
        ("La Rochelle", "rugby", "La Rochelle", "club"),
        ("RC Toulon", "rugby", "Toulon", "club"),
        ("Union Bordeaux-Bègles", "rugby", "UBB", "club"),
        ("USA Perpignan", "rugby", "Perpignan", "club"),

        # NBA
        ("Los Angeles Lakers", "basket", "Lakers", "club"),
        ("Lakers", "basket", "Lakers", "club"),
        ("Boston Celtics", "basket", "Celtics", "club"),
        ("Golden State Warriors", "basket", "Warriors", "club"),

        # Tennis players
        ("N. Djokovic", "tennis", "Djokovic", "player"),
        ("C. Alcaraz", "tennis", "Alcaraz", "player"),
        ("Novak Djokovic", "tennis", "Djokovic", "player"),
        ("J. Sinner", "tennis", "Sinner", "player"),

        # MMA
        ("Francis Ngannou", "mma", "Ngannou", "player"),
        ("Tyson Fury", "mma", "Fury", "player"),

        # National teams
        ("France", "football", "France", "country"),
        ("Colombie", "football", "Colombie", "country"),
        ("Brésil", "football", "Brésil", "country"),
        ("Danemark", "football", "Danemark", "country"),
        ("Allemagne", "football", "Allemagne", "country"),
        ("Maroc", "football", "Maroc", "country"),
    ]

    passed = 0
    failed = 0

    print(f"\n{'━' * 64}")
    print(f"  MATCHING TESTS ({len(test_cases)} cases)")
    print(f"{'━' * 64}\n")

    for raw_name, sport, expected_short, expected_type in test_cases:
        profile = match_entity(raw_name, sport)

        if not profile:
            print(f"  ❌ '{raw_name}' ({sport}) → NOT FOUND (expected {expected_short})")
            errors.append(f"No match for '{raw_name}'")
            failed += 1
            continue

        ok_short = profile.short_name == expected_short
        ok_type = profile.entity_type == expected_type

        if ok_short and ok_type:
            print(f"  ✅ '{raw_name}' → {profile.short_name} [{profile.entity_type}]"
                  f"{'  🖼️' if profile.logo_url or profile.photo_url else ''}")
            passed += 1
        else:
            issues = []
            if not ok_short:
                issues.append(f"short={profile.short_name}, expected={expected_short}")
            if not ok_type:
                issues.append(f"type={profile.entity_type}, expected={expected_type}")
            print(f"  ⚠️  '{raw_name}' → {profile.short_name} [{profile.entity_type}] — {', '.join(issues)}")
            errors.append(f"Mismatch for '{raw_name}': {', '.join(issues)}")
            failed += 1

    # ── Enrichment test ──
    print(f"\n{'━' * 64}")
    print(f"  ENRICHMENT TEST")
    print(f"{'━' * 64}\n")

    raw_entity = {"name": "Paris-SG", "type": "club", "country_code": None}
    enriched = enrich_entity(raw_entity, "football")
    print(f"  Input:  {raw_entity}")
    print(f"  Output: {enriched}")

    if enriched.get("name") != "Paris Saint-Germain":
        errors.append(f"Enrichment name wrong: {enriched.get('name')}")
    if enriched.get("short") != "PSG":
        errors.append(f"Enrichment short wrong: {enriched.get('short')}")
    if not enriched.get("logo_url"):
        errors.append("Enrichment missing logo_url")
    if enriched.get("country_code") != "fr":
        errors.append(f"Enrichment country wrong: {enriched.get('country_code')}")

    # ── Summary ──
    print(f"\n{'━' * 64}")
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")

    if errors:
        print(f"\n  ❌ Errors:")
        for e in errors:
            print(f"     • {e}")
    else:
        print(f"\n  ✅ ALL TESTS PASSED")
    print(f"{'━' * 64}")

    return len(errors) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
