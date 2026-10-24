"""
Écussons : repli sur les équipes du calendrier ESPN (data/espn_teams.json).
Lancer : cd backend && python tests/test_espn_fallback.py   (ou pytest)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.entity_registry import enrich_entity  # noqa: E402


def logo_id(name, sport="football"):
    e = enrich_entity({"name": name, "type": "club"}, sport)
    url = e.get("logo_url") or ""
    return int(url.rsplit("/", 1)[-1].split(".")[0]) if url else None


def test_french_names_resolve_to_the_right_crest():
    cases = {
        "Fribourg": 126, "Mayence": 2950, "Cologne": 122, "Augsbourg": 3841, "Hambourg": 127,
        "Werder Brême": 137, "Bologne": 107, "Magdebourg": 10382, "Dynamo Dresde": 7017,
        "Borussia Monchengladbach": 268, "Eintracht Francfort": 125, "Hertha Berlin": 129,
        "Union Berlin": 598, "Brighton & Hove Albion": 331, "West Bromwich Albion": 383,
        "Galatasaray": 432, "Nacional Madeira": 3472, "Boulogne-sur-Mer": 7869,
        "Elverberg": 10388,                      # faute de frappe du flux TV
        "Valence": 94, "Deportivo La Corogne": 90, "Tenerife": 245, "Paris FC": 6851,
    }
    for name, expected in cases.items():
        assert logo_id(name) == expected, (name, logo_id(name), expected)


def test_unknown_or_ambiguous_clubs_get_no_crest():
    for name in ("Bastia", "Caen", "Essen", "Chicago Bears", "Sonnenhf"):
        assert logo_id(name) is None, name


def test_lookalikes_are_not_confused():
    assert logo_id("Manchester City") != logo_id("Manchester United")
    assert logo_id("Union Berlin") != logo_id("Union Saint-Gilloise")
    assert logo_id("Real Sociedad") == 89


def test_registry_crest_ids_match_the_club():
    """Chaque écusson ESPN du registre doit être celui du club (id ↔ nom), pas celui d'un voisin."""
    import json, re
    from app.entity_registry import ENTITY_REGISTRY
    from app.fixtures import name_score
    teams = {t["id"]: t for t in json.loads((Path(__file__).parent.parent / "data" / "espn_teams.json").read_text("utf-8"))}
    bad = []
    for p in ENTITY_REGISTRY:
        m = re.search(r"/soccer/500/(\d+)\.png", p.logo_url or "")
        if p.entity_type != "club" or p.sport != "football" or not m:
            continue
        team = teams.get(int(m.group(1)))
        if team is None:
            continue            # club hors des championnats suivis : non vérifiable
        names = [team["name"], team["short"]] if team["short"] else [team["name"]]
        if max(name_score(c, names) for c in [p.canonical_name, p.short_name, *p.aliases]) < 0.9:
            bad.append((p.canonical_name, team["name"]))
    assert not bad, bad


def run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t(); passed += 1; print(f"  ✓ {t.__name__}")
        except AssertionError as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n  RESULTS: {passed}/{len(tests)} passed, {len(tests) - passed} failed")
    return passed == len(tests)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
