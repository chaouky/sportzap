"""
Sports sans équipes : rediffusions (F1 via séances ESPN, cyclisme, ski), noms de GP,
classement des disciplines et découpage des titres.
Les cas viennent du programme réel du 24-30/10/2026.

Lancer : cd backend && python tests/test_solo_sports.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.fixtures import Session, parse_f1_scoreboard  # noqa: E402
from app.models import Channel, SportEvent, SportType  # noqa: E402
from app.schedule_refine import f1_session_kind, refine_events  # noqa: E402
from app.sport_extractor import classify_sport, extract_matchup, extract_sport_events  # noqa: E402

PARIS = ZoneInfo("Europe/Paris")
NOW = datetime(2026, 10, 24, 12, 0, tzinfo=PARIS)
_n = 0


def solo(sport, title, subtitle, start, minutes, channel="Eurosport 2"):
    global _n
    _n += 1
    return SportEvent(
        id=f"s{_n}", sport=SportType(sport), title=title, subtitle=subtitle,
        channel=Channel(id=f"{channel}.fr", name=channel, slug=channel.lower().replace(" ", "-")),
        start=start, end=start + timedelta(minutes=minutes),
    )


def at(day, hh, mm=0):
    return datetime(2026, 10, day, hh, mm, tzinfo=PARIS)


def titles(events):
    return [(e.title, e.start.strftime("%d %H:%M")) for e in events]


# ───────────── cyclisme ─────────────

def test_old_race_rebroadcasts_are_dropped():
    # Gran Piemonte (couru le 8 octobre) : 6 repassages courts, de nuit ou en soirée
    airings = [(24, 0, 6, 83), (24, 2, 30, 90), (24, 5, 0, 90), (24, 10, 0, 90), (24, 18, 0, 90), (24, 22, 0, 60)]
    evs = [solo("cyclisme", "Gran Piemonte", "Asti - Bra (185,3km)", at(d, h, m), mn) for d, h, m, mn in airings]
    out, stats = refine_events(evs, now=NOW)
    assert out == [], titles(out)
    assert stats["drop_replay_solo"] == 6


def test_live_cycling_is_kept_once():
    live = solo("cyclisme", "Tour de Lombardie", "Bergamo - Como (239km)", at(24, 13, 30), 270)
    live2 = solo("cyclisme", "Tour de Lombardie", "Bergamo - Como (239km)", at(24, 13, 30), 270, "Eurosport 1")
    replay = solo("cyclisme", "Tour de Lombardie", "Bergamo - Como (239km)", at(25, 2, 30), 90)
    replay2 = solo("cyclisme", "Tour de Lombardie", "Bergamo - Como (239km)", at(25, 21, 0), 120)
    out, _ = refine_events([live, live2, replay, replay2], now=NOW)
    assert [e.id for e in out] == [live.id, live2.id]


# ───────────── ski ─────────────

def test_ski_keeps_the_live_run_and_its_simulcast():
    live = solo("ski", "Sölden | Slalom Géant (F) - 1re manche", "Coupe du monde FIS", at(24, 9, 30), 120, "Eurosport 360 - 2")
    live1 = solo("ski", "Sölden | Slalom Géant (F) - 1re manche", "Coupe du monde FIS", at(24, 9, 40), 110, "Eurosport 1")
    again = solo("ski", "Sölden | Slalom Géant (F) - 1re manche", "Coupe du monde FIS", at(24, 16, 15), 45)
    night = solo("ski", "Sölden | Slalom Géant (F) - 1re manche", "Coupe du monde FIS", at(25, 1, 0), 45)
    out, _ = refine_events([live, live1, again, night], now=NOW)
    assert {e.id for e in out} == {live.id, live1.id}


# ───────────── F1 ─────────────

SESSIONS = [
    Session(datetime(2026, 10, 23, 21, 0, tzinfo=timezone.utc), "FP2"),
    Session(datetime(2026, 10, 24, 17, 30, tzinfo=timezone.utc), "FP3"),
    Session(datetime(2026, 10, 24, 21, 0, tzinfo=timezone.utc), "Qual"),
    Session(datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc), "Race"),
]


def f1(title, start, minutes, channel="Canal+ Sport 5", sub="Grand Prix des Etats-Unis"):
    return solo("f1", title, sub, start, minutes, channel)


def test_f1_session_kinds():
    k = lambda t, s="Grand Prix des Etats-Unis": f1_session_kind(f1(t, at(24, 12), 60, sub=s))  # noqa: E731
    assert k("Essais libres 2") == "FP2" and k("Essais qualificatifs") == "Qual" and k("La course") == "Race"
    assert k("Formule 1 : Grand Prix des Etats-Unis", "Grand Prix des Etats-Unis. La course. Ch") == "Race"
    assert k("Feature Race") == "" and k("1re course") == "" and k("2e course") == ""


def test_f1_replays_are_dropped_with_official_sessions():
    live_quali = f1("Essais qualificatifs", at(24, 22, 38), 104)             # avant-show de 22 min
    quali_again = f1("Essais qualificatifs", at(25, 10, 16), 104, "Canal+ Sport 360")
    fp2_replays = [f1("Essais libres 2", at(24, 4, 30), 130), f1("Essais libres 2", at(24, 9, 52), 87, "Canal+ Sport 360")]
    race_live = [f1("La course", at(25, 20, 59), 105, "Canal+ Live 19"), f1("La course", at(25, 21, 0), 106)]
    race_replays = [f1("La course", at(25, 23, 19), 107, "Canal+"), f1("La course", at(26, 13, 8), 110)]
    evs = [live_quali, quali_again, *fp2_replays, *race_live, *race_replays]
    out, stats = refine_events(evs, now=NOW, sessions=SESSIONS)
    assert {e.id for e in out} == {live_quali.id, *(e.id for e in race_live)}, titles(out)
    ko = {e.id: e.kickoff for e in out}
    assert ko[live_quali.id] == datetime(2026, 10, 24, 23, 0, tzinfo=PARIS)        # 21:00Z
    assert ko[race_live[0].id] == datetime(2026, 10, 25, 21, 0, tzinfo=PARIS)      # 20:00Z (heure d'hiver)
    assert stats["drop_replay_session"] == 5


def test_f1_without_sessions_keeps_the_first_airing_only():
    evs = [f1("La course", at(25, 21, 0), 106), f1("La course", at(25, 23, 19), 107, "Canal+"),
           f1("La course", at(26, 13, 8), 110)]
    out, _ = refine_events(evs, now=NOW)
    assert [e.id for e in out] == [evs[0].id]


def test_f1_academy_and_other_gp_untouched_by_sessions():
    academy = f1("Feature Race", at(25, 17, 55), 41, "Canal+ Sport 360")
    out, _ = refine_events([academy], now=NOW, sessions=SESSIONS)
    assert [e.id for e in out] == [academy.id]


def test_parse_f1_scoreboard():
    data = {"events": [{"name": "US GP", "competitions": [
        {"date": "2026-10-24T21:00Z", "type": {"abbreviation": "Qual"}, "status": {"type": {"state": "in"}}},
        {"date": "2026-10-23T21:00Z", "type": {"abbreviation": "FP2"}},
        {"date": "2026-10-23T21:00Z", "type": {"abbreviation": "???"}},
    ]}]}
    out = parse_f1_scoreboard(data)
    assert [(s.kind, s.start.hour) for s in out] == [("Qual", 21), ("FP2", 21)]


# ───────────── classement des disciplines ─────────────

def prog(title, subtitle=None, categories=("sport",), desc=None):
    return {"title": title, "subtitle": subtitle, "description": desc, "categories": list(categories)}


def test_judo_and_skating_are_not_mma_or_ski():
    assert classify_sport(prog("Judo : Ligue des champions par équipes", categories=("sport de combat",))) == SportType.OTHER
    assert classify_sport(prog("Patinage artistique : Grand Prix de France", categories=("sports d'hiver",))) == SportType.OTHER
    assert classify_sport(prog("MMA : UFC | A / B", categories=("sport de combat",))) == SportType.MMA
    assert classify_sport(prog("Ski alpin : Coupe du monde", categories=("sports d'hiver",))) == SportType.SKI


def test_nfl_is_its_own_sport_and_motogp_is_not_f1():
    assert classify_sport(prog("Football américain : NFL | Saints / Steelers", categories=("football",))) == SportType.FOOTBALL_US
    assert classify_sport(prog("Moto GP : Grand Prix d'Australie", categories=("auto-moto",))) == SportType.MOTOGP
    assert classify_sport(prog("Football : Ligue 1 | Lens / Paris FC", categories=("football",))) == SportType.FOOTBALL


def test_sport_named_before_the_colon_wins():
    assert classify_sport(prog("Voile : Grand Prix de Genève", categories=("sport mécanique",))) == SportType.VOILE
    assert classify_sport(prog("Formule 1 : Grand Prix des Etats-Unis", categories=("sport mécanique",))) == SportType.F1


def test_presentations_and_onboard_shows_are_not_events():
    from app.sport_extractor import is_actual_match
    assert not is_actual_match(prog("Cyclisme : Tour de France | Tour de France. Présentation du parcours"))
    assert not is_actual_match(prog("On Board F1", "ÉTATS-UNIS"))


# ───────────── titres ─────────────

def test_ufc_title_suffix_is_not_part_of_the_fighter_name():
    t1, t2 = extract_matchup(prog("MMA : UFC | Alexander Volkanovski / Movsar Evloev et Poids coqs"), SportType.MMA)
    assert (t1.name, t2.name) == ("Alexander Volkanovski", "Movsar Evloev")


def test_player_initials_are_not_cut():
    t1, t2 = extract_matchup(prog("Tennis : Masters 1000 de Miami | N. Djokovic (SRB) / C. Alcaraz (ESP)"), SportType.TENNIS)
    assert (t1.name, t2.name) == ("N. Djokovic", "C. Alcaraz")
    t1, t2 = extract_matchup(prog("Basket : Euroligue | Real Madrid. Euroligue masculine. 36e journée. / Olympiacos"), SportType.BASKET)
    assert t1.name == "Real Madrid"


def test_generic_title_needs_a_matchup_in_the_subtitle():
    from app.sport_extractor import is_actual_match
    assert is_actual_match(prog("Football", "Monaco - Lens"))
    assert not is_actual_match(prog("Football", None))
    assert not is_actual_match(prog("Rugby", "Magazine"))


def test_h_f_in_parentheses_is_not_a_matchup():
    assert extract_matchup(prog("Santiago | Difficulté (H/F) - Finale", "World Climbing Series"), SportType.OTHER) == (None, None)


def test_grand_prix_name_comes_from_subtitle():
    start = datetime(2026, 10, 24, 17, 15, tzinfo=timezone.utc)
    p = {"channel_id": "CanalPlusSport5.fr", "start": start, "end": start + timedelta(minutes=86),
         "title": "Essais libres 3", "subtitle": "Grand Prix des Etats-Unis", "description": None,
         "categories": ["sport mécanique"]}
    out = extract_sport_events([p], {"CanalPlusSport5.fr": {"id": "CanalPlusSport5.fr", "name": "CANAL+ SPORT 5"}})
    assert len(out) == 1 and out[0].competition == "Grand Prix des États-Unis"


def run():
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
