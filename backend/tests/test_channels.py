"""Channel normalization + French-only filter (no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.sport_extractor import build_channel, is_french_channel

CASES = [
    # (id, name, expected_slug, expected_french)
    ("LEquipe21.fr", "La chaine l’Équipe", "lequipe", True),
    ("Ligue1Plus.fr", "Ligue 1+", "ligue-1", True),
    ("Ligue1Plus7.fr", "Ligue 1+ 7", "ligue-1", True),
    ("InfosportPlus.fr", "InfosportPlus", "infosport-plus", True),
    ("CanalPlusSport2.af", "Canal+ Sport 2", "canal-plus-sport-2", False),
    ("CanalPlusSport1.af", "Canal+ Sport 1", "canal-plus-sport", False),
    ("CanalPlusSport.fr", "Canal+ Sport", "canal-plus-sport", True),
    ("CanalPlusSport.ch", "Canal+ Sport", "canal-plus-sport", False),
    ("CanalPlusLive11.fr", "Canal+ Live 11", "canal-plus-live", True),
    ("Eurosport3602.fr", "Eurosport 360 - 2", "eurosport-360", True),
    ("beINSPORTSMAX1.fr", "beIN SPORTS MAX 1", "bein-1", True),
    ("beINSPORTSMAX9.fr", "beIN SPORTS MAX 9", "bein-max", True),
    ("ElevenProL1.be", "ElevenProL1", "elevenprol1", False),
    ("VOOSportWorld1.be", "VOO Sport World 1", "voo-sport-world-1", False),
    ("TVASports.ca", "TVA Sports", "tva-sports", False),
    ("TV5Monde.fr", "TV5 Monde", "tv5-monde", False),
    ("GolfPlus.fr", "Golf+", "golf", True),
]


def run():
    failed = 0
    for cid, name, slug, french in CASES:
        ch = build_channel({"id": cid, "name": name})
        ok = ch.slug == slug and is_french_channel(ch) == french
        if not ok:
            failed += 1
            print(f"  FAIL {cid!r} {name!r}: slug={ch.slug!r} french={is_french_channel(ch)}")
    print(f"  RESULTS: {len(CASES) - failed}/{len(CASES)} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
