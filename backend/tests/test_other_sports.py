"""Logos des clubs hors football : NBA/NFL/NHL/MLB (ESPN), rugby, basket, handball, volley, hockey."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.entity_registry import enrich_entity  # noqa: E402


def logo(name, sport, type_="club"):
    return (enrich_entity({"name": name, "type": type_}, sport) or {}).get("logo_url") or ""


def test_us_leagues():
    assert "/nba/" in logo("Miami Heat", "basket")
    assert "/nhl/" in logo("Anaheim Ducks", "other")
    assert "/mlb/" in logo("Tampa Bay Rays", "other")
    # NFL est classé « football » par le flux ; « Los Angeles Rams » ne doit pas devenir LAFC
    assert "/nfl/" in logo("Los Angeles Rams", "foot_us")
    assert "/nfl/" in logo("Baltimore Ravens", "foot_us")
    assert "/nfl/" not in logo("Los Angeles FC", "football")


def test_french_clubs_other_sports():
    assert "wikimedia" in logo("Limoges", "basket")
    assert "wikimedia" in logo("Pau-Orthez", "basket")
    assert "wikimedia" in logo("Chambéry", "handball")
    assert "wikimedia" in logo("Saint-Raphaël", "handball")
    assert "wikimedia" in logo("RC Cannes", "volleyball")
    assert "wikimedia" in logo("RC Vannes", "rugby")


def test_same_name_other_sport_is_not_the_football_club():
    # « Lyon » en basket = ASVEL féminin, pas l'OL ; « Nantes » en handball = HBC Nantes, pas le FCN
    assert "soccer" not in logo("Lyon", "basket")
    assert "soccer" not in logo("Nantes", "handball")
    assert "soccer" in logo("Lyon", "football")


def test_wnba_franchise_is_not_the_nba_team():
    # « Golden State Valkyries » (WNBA) était rapproché des Warriors par sous-chaîne
    e = enrich_entity({"name": "Golden State Valkyries", "type": "club"}, "basket")
    assert e["name"] == "Golden State Valkyries" and "/wnba/" in e["logo_url"]
    assert "/nba/" in logo("Golden State Warriors", "basket")
    assert "/wnba/" in logo("Atlanta Dream", "basket")


def test_ligue2_and_euroleague_clubs_have_a_logo():
    for name, sport in [("Amiens", "football"), ("Caen", "football"), ("Bastia", "football"),
                        ("Caja Laboral Baskonia", "basket"), ("Efes Pilsen", "basket")]:
        assert "wikimedia" in logo(name, sport), name
    assert "soccer" in logo("Lens", "football")


def test_national_teams_get_a_flag():
    assert logo("Nouvelle-Zélande", "rugby", "country").endswith("/nz.png")


def test_unknown_club_has_no_logo():
    assert logo("Club Inconnu Des Etoiles", "basket") == ""


def test_no_dead_rugby_crest_urls():
    """Les anciens chemins ESPN /rugby/500/{id}.png renvoient 404 : aucun logo ne doit les utiliser."""
    from app import entity_registry as er
    from app.entity_registry import _other_teams
    urls = [getattr(p, "logo_url", None) for p in er.ENTITY_REGISTRY] if hasattr(er, "ENTITY_REGISTRY") else []
    urls += [t.get("logo") for t in _other_teams()] if isinstance(_other_teams(), list) else []
    assert not [u for u in urls if u and "/rugby/500/" in u]
    assert "countries/500/usa.png" not in " ".join(u for u in urls if u)
    assert "rugby/teams/500/25922.png" in logo("Stade Toulousain", "rugby")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
