"""
Tests de l'affinage du programme : coup d'envoi réel et rediffusions.
Les cas viennent du programme réel du 24/10/2026.

Lancer : cd backend && python -m pytest tests/test_schedule_refine.py -v
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.fixtures import Fixture, _parse_espn_date, name_score, parse_scoreboard  # noqa: E402
from app.models import Channel, Entity, EventStatus, SportEvent, SportType  # noqa: E402
from app.schedule_refine import estimate_kickoff, refine_events, streaming_fixtures  # noqa: E402

PARIS = ZoneInfo("Europe/Paris")
NOW = datetime(2026, 10, 24, 18, 25, tzinfo=PARIS)


def paris(day, hh, mm=0):
    return datetime(2026, 10, day, hh, mm, tzinfo=PARIS)


_n = 0


def ev(t1, t2, start, minutes=105, comp="Ligue 1 McDonald's", channel="Canal+ Sport 1",
       sport="football", desc=None, subtitle=None):
    global _n
    _n += 1
    return SportEvent(
        id=f"e{_n}", sport=SportType(sport), competition=comp,
        title=f"{t1} / {t2}", subtitle=subtitle, description=desc,
        team1=Entity(name=t1, type="club"), team2=Entity(name=t2, type="club"),
        channel=Channel(id=f"{channel}.fr", name=channel, slug=channel.lower().replace(" ", "-")),
        start=start, end=start + timedelta(minutes=minutes),
    )


def fx(h, a, when_utc, state="pre"):
    return Fixture(start=when_utc, home=[h], away=[a], state=state)


# ───────────── ESPN : parsing ─────────────

def test_parse_espn_date_variants():
    assert _parse_espn_date("2026-10-24T18:45Z") == datetime(2026, 10, 24, 18, 45, tzinfo=timezone.utc)
    assert _parse_espn_date("2026-10-24T18:45:00Z").hour == 18


def test_parse_scoreboard():
    data = {"events": [{
        "id": "1", "date": "2026-10-24T18:45Z",
        "status": {"type": {"state": "pre"}},
        "competitions": [{"competitors": [
            {"homeAway": "home", "team": {"displayName": "Lens", "shortDisplayName": "Lens"}},
            {"homeAway": "away", "team": {"displayName": "Paris FC", "shortDisplayName": "Paris FC"}},
        ]}],
    }, {"id": "2", "date": "bad"}]}
    out = parse_scoreboard(data, "fra.1")
    assert len(out) == 1 and out[0].home == ["Lens"] and out[0].start.hour == 18


# ───────────── noms d'équipes ─────────────

def test_name_matching():
    ok = [("Paris-SG", "Paris Saint-Germain"), ("Valence", "Valencia"), ("Stade Toulousain", "Toulouse"),
          ("Betis Séville", "Real Betis"), ("Olympique Lyonnais", "OL Lyonnes"), ("Fribourg", "SC Freiburg"),
          ("Augsbourg", "FC Augsburg"), ("Le Havre", "Le Havre AC"), ("Olympique de Marseille", "Marseille")]
    for tv, espn in ok:
        assert name_score(tv, [espn]) >= 0.78, (tv, espn)


def test_name_matching_rejects_lookalikes():
    bad = [("Manchester City", "Manchester United"), ("Paris-SG", "Paris FC"),
           ("Real Madrid", "Real Betis"), ("Atlético Madrid", "Real Madrid")]
    for tv, espn in bad:
        assert name_score(tv, [espn]) < 0.78, (tv, espn)


# ───────────── calendrier officiel ─────────────

def test_live_broadcast_gets_official_kickoff():
    # Lens–Paris FC : Canal+ commence à 20h40, coup d'envoi officiel 20h45
    e = ev("RC Lens", "Paris FC", paris(24, 20, 40), 140)
    out, st = refine_events([e], [fx("Lens", "Paris FC", datetime(2026, 10, 24, 18, 45, tzinfo=timezone.utc))], NOW)
    assert len(out) == 1 and st["espn_matched"] == 1
    assert out[0].kickoff.astimezone(PARIS).strftime("%H:%M") == "20:45"
    assert out[0].kickoff_source == "espn"


def test_official_kickoff_beats_estimate():
    # DAZN annonce 20h45 mais le match est à 21h00 : l'estimation seule se tromperait
    e = ev("Atlético Madrid", "Deportivo La Corogne", paris(24, 20, 45), 135, "Liga", "DAZN 1")
    out, _ = refine_events([e], [fx("Atlético Madrid", "Deportivo La Coruña",
                                    datetime(2026, 10, 24, 19, 0, tzinfo=timezone.utc))], NOW)
    assert out[0].kickoff.astimezone(PARIS).strftime("%H:%M") == "21:00"


def test_replay_after_official_kickoff_is_dropped():
    # Brest–Nice a été joué vendredi 20h45 : les diffusions de samedi sont des rediffusions
    f = fx("Brest", "Nice", datetime(2026, 10, 23, 18, 45, tzinfo=timezone.utc), "post")
    e1 = ev("Stade Brestois", "OGC Nice", paris(24, 12, 17), 102)
    e2 = ev("Stade Brestois", "OGC Nice", paris(24, 18, 4), 86, channel="Ligue 1+")
    out, st = refine_events([e1, e2], [f], NOW)
    assert out == [] and st["drop_replay_espn"] == 2


def test_other_week_fixture_is_not_a_replay_signal():
    # Le match est dans 2 jours : une diffusion aujourd'hui n'est ni « direct » ni « replay »
    f = fx("Brest", "Nice", datetime(2026, 10, 26, 18, 45, tzinfo=timezone.utc))
    out, _ = refine_events([ev("Brest", "Nice", paris(24, 20, 0))], [f], NOW)
    assert len(out) == 1


# ───────────── filtres sans calendrier ─────────────

def test_short_preshow_dropped():
    out, st = refine_events([ev("Lyon", "Marseille", paris(24, 20, 31), 24, comp=None, channel="Canal+ Foot")], [], NOW)
    assert out == [] and st["drop_short"] == 1


def test_replay_wording_dropped_but_boilerplate_kept():
    replay = ev("Hoffenheim", "Lyon", paris(24, 18, 0), 120, "Ligue Europa", "OLPLAY",
                desc="Revivez la rencontre entre Hoffenheim et l'OL lors de la 3ème journée.")
    live = ev("Napoli", "Roma", paris(24, 17, 50), 130, "Serie A", "DAZN 1",
              desc="Retransmission d'un match du championnat d'Italie de football, appelé Serie A.")
    out, _ = refine_events([replay, live], [], NOW)
    assert [o.id for o in out] == [live.id]


def test_partial_period_dropped():
    e = ev("Brest", "Nice", paris(24, 18, 4), 86, channel="Ligue 1+",
           desc="1ère période du match de la Journée 8 du Championnat de France de Ligue 1 McDonald's 2026/27 opposant Brest et Nice")
    assert refine_events([e], [], NOW)[0] == []


def test_archive_season_dropped_but_generic_text_kept():
    classic = ev("Paris-SG", "Lyon", paris(25, 14, 5), 120, channel="Ligue 1+",
                 desc="Match de la 30ème journée du Championnat de France de Ligue 1 McDonald's 2025/26 opposant PARIS SG et OL.")
    generic = ev("Lens", "Paris FC", paris(24, 20, 40), 140,
                 desc="… Ligue 1 McDonald's à partir de la saison 2024/2025.")
    out, _ = refine_events([classic, generic], [], NOW)
    assert [o.id for o in out] == [generic.id]


def test_european_football_at_night_is_replay():
    night = ev("Bayern Munich", "Arsenal", paris(24, 1, 36), 99, "Ligue des champions")
    day = ev("Chelsea", "Tottenham", paris(24, 18, 25), 125, "Premier League")
    out, st = refine_events([night, day], [], NOW)
    assert [o.id for o in out] == [day.id] and st["drop_replay_night"] == 1


def test_night_rule_spares_non_european_competitions():
    nba = ev("Charlotte Hornets", "Miami Heat", paris(25, 1, 0), 150, "NBA", "Canal+ Sport 1", sport="basket")
    out, _ = refine_events([nba], [], NOW)
    assert len(out) == 1


def test_later_waves_are_replays():
    first = ev("Elversberg", "Leipzig", paris(24, 15, 25), 124)
    second = ev("Elversberg", "Leipzig", paris(24, 23, 16), 104, channel="Canal+ Sport 2")
    same_wave = ev("Elversberg", "Leipzig", paris(24, 15, 24), 126, channel="beIN SPORTS MAX 4")
    out, st = refine_events([first, second, same_wave], [], NOW)
    assert {o.id for o in out} == {first.id, same_wave.id} and st["drop_replay_wave"] == 1


def test_different_round_is_a_different_match():
    a = ev("Paris-SG", "Lyon", paris(25, 20, 40), 118, subtitle="Ligue 1 McDonald's - 8e journée")
    b = ev("Paris-SG", "Lyon", paris(28, 21, 0), 118, subtitle="Ligue 1 McDonald's - 12e journée")
    out, _ = refine_events([a, b], [], NOW)
    assert len(out) == 2


def test_individual_sports_untouched():
    t = SportEvent(id="t1", sport=SportType("tennis"), title="Tennis : Masters", competition="ATP",
                   channel=Channel(id="E1.fr", name="Eurosport 1", slug="eurosport-1"),
                   start=paris(25, 3, 0), end=paris(25, 5, 0))
    out, _ = refine_events([t], [], NOW)
    assert len(out) == 1 and out[0].kickoff is None


# ───────────── estimation du coup d'envoi ─────────────

def test_estimate_rounds_up_to_next_quarter():
    assert estimate_kickoff(paris(24, 15, 24))[0] == paris(24, 15, 30)
    assert estimate_kickoff(paris(24, 15, 55))[0] == paris(24, 16, 0)
    assert estimate_kickoff(paris(24, 20, 45))[0] == paris(24, 20, 45)   # déjà un quart d'heure
    assert estimate_kickoff(paris(24, 19, 30))[0] == paris(24, 19, 30)
    assert estimate_kickoff(paris(24, 20, 31))[0] == paris(24, 20, 31)   # trop loin du quart : on garde


def test_estimated_kickoff_is_shared_across_channels():
    a = ev("Dortmund", "Frankfurt", paris(24, 18, 25), 125, "Bundesliga", "Canal+ Sport 1")
    b = ev("Dortmund", "Frankfurt", paris(24, 18, 30), 120, "Bundesliga", "beIN SPORTS 2")
    out, _ = refine_events([a, b], [], NOW)
    assert {o.kickoff.astimezone(PARIS).strftime("%H:%M") for o in out} == {"18:30"}
    assert all(o.kickoff_source == "estimate" for o in out)


# ───────────── matchs sans diffuseur connu ─────────────

def lfx(h, a, when_utc, state="pre", league="esp.1", i="1"):
    return Fixture(start=when_utc, home=[h], away=[a], state=state, league=league, id=i)


def test_streaming_liga_fixtures_are_added_per_platform():
    tv = ev("Valence", "Villarreal", paris(24, 18, 25), 125, "Liga", "Canal+ Sport 4")
    fixtures = [
        lfx("Valencia", "Villarreal", datetime(2026, 10, 24, 16, 30, tzinfo=timezone.utc), i="1"),
        lfx("Getafe", "Athletic Club", datetime(2026, 10, 25, 13, 0, tzinfo=timezone.utc), i="2"),
        lfx("Elche", "Rayo Vallecano", datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc), "post", i="3"),
        lfx("Lens", "Paris FC", datetime(2026, 10, 25, 13, 0, tzinfo=timezone.utc), league="fra.1", i="4"),
    ]
    out, _ = refine_events([tv], fixtures, NOW)
    extra = streaming_fixtures(out, fixtures, NOW)
    got = sorted((e.team1.name.split()[0], e.channel.slug) for e in extra)
    # Getafe : DAZN + Disney+ ; Valence : Canal+ est déjà au programme mais pas DAZN/Disney+
    assert got == [("Getafe", "dazn"), ("Getafe", "disney-plus"),
                   ("Valence", "dazn"), ("Valence", "disney-plus")], got
    g = next(e for e in extra if e.team1.name.startswith("Getafe"))
    assert g.kickoff.astimezone(PARIS).strftime("%d %H:%M") == "25 14:00"
    assert g.kickoff_source == "espn" and g.status == EventStatus.UPCOMING


def test_streaming_not_duplicated_when_platform_already_in_feed():
    dz = ev("Atlético Madrid", "Deportivo La Corogne", paris(24, 20, 45), 135, "Liga", "DAZN 1")
    f = lfx("Atlético Madrid", "Deportivo", datetime(2026, 10, 24, 19, 0, tzinfo=timezone.utc))
    out, _ = refine_events([dz], [f], NOW)
    slugs = sorted(e.channel.slug for e in streaming_fixtures(out, [f], NOW))
    assert slugs == ["disney-plus"], slugs


def test_replay_of_previous_round_dropped_with_wider_calendar():
    # Espanyol–Atlético (journée 9) joué mercredi dernier, rediffusé lundi 23h33
    f = lfx("Espanyol", "Atlético Madrid", datetime(2026, 10, 21, 19, 0, tzinfo=timezone.utc), "post")
    e = ev("Espanyol Barcelone", "Atlético Madrid", paris(26, 23, 33), 120, "Liga", "Canal+ Sport 3")
    out, st = refine_events([e], [f], NOW)
    assert out == [] and st["drop_replay_espn"] == 1


# ───────────── classification / filtres de contenu ─────────────

def test_motogp_not_classified_as_f1():
    from app.sport_extractor import classify_sport
    prog = {"title": "Moto GP : Grand Prix d'Australie", "categories": ["auto-moto"]}
    assert classify_sport(prog) == SportType.MOTOGP
    assert classify_sport({"title": "Formule 1 : Grand Prix du Mexique", "categories": ["auto-moto"]}) == SportType.F1


def test_shows_are_not_events():
    from app.sport_extractor import is_actual_match
    for title in ("Is+ Image du jour : Formule 1", "Sports Week-end", "Club Week-end",
                  "Le podium", "La grille", "Match of ze Day", "Histoire de Champions"):
        assert not is_actual_match({"title": title, "categories": ["sport"]}), title
    assert is_actual_match({"title": "La course", "subtitle": "Grand Prix des Etats-Unis",
                            "categories": ["sport"]}) in (True, False)  # ne plante pas


# ───────────── statut ─────────────

def test_status_follows_kickoff_not_broadcast_start():
    # Antenne ouverte à 18h25, coup d'envoi 18h30, il est 18h27 → pas encore « en direct »
    e = ev("Chelsea", "Tottenham", paris(24, 18, 25), 125, "Premier League")
    out, _ = refine_events([e], [fx("Chelsea", "Tottenham", datetime(2026, 10, 24, 16, 30, tzinfo=timezone.utc))],
                           datetime(2026, 10, 24, 18, 27, tzinfo=PARIS))
    assert out[0].status == EventStatus.UPCOMING
    out, _ = refine_events([e], [fx("Chelsea", "Tottenham", datetime(2026, 10, 24, 16, 30, tzinfo=timezone.utc))],
                           datetime(2026, 10, 24, 18, 31, tzinfo=PARIS))
    assert out[0].status == EventStatus.LIVE


def run():
    """Exécution sans pytest (CI : python tests/test_schedule_refine.py)."""
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {name}: {exc!r}")
    print(f"  RESULTS: {len(tests) - failed}/{len(tests)} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
