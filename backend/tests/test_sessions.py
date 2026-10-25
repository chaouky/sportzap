"""
Séances et épreuves sans affiche (MotoGP/Moto2/Moto3, F1, tennis, golf, padel…),
rediffusions de ces épreuves, doublons Euroligue, robustesse ESPN.
Les cas viennent du programme réel du 23/10 au 1/11/2026.

Lancer : cd backend && python tests/test_sessions.py
"""
import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import fixtures  # noqa: E402
from app.models import Channel, Entity, SportEvent, SportType  # noqa: E402
from app.schedule_refine import refine_events  # noqa: E402
from app.sport_extractor import (  # noqa: E402
    classify_sport, extract_sport_events, normalize_session_event,
)

PARIS = ZoneInfo("Europe/Paris")
NOW = datetime(2026, 10, 25, 1, 0, tzinfo=PARIS)
_n = 0


def at(day, hh, mm=0, month=10):
    return datetime(2026, month, day, hh, mm, tzinfo=PARIS)


def prog(title, subtitle, categories, start, minutes=60, channel="CanalPlusSport2.fr", desc=""):
    return {"channel_id": channel, "title": title, "subtitle": subtitle, "description": desc,
            "categories": categories, "start": start, "end": start + timedelta(minutes=minutes)}


CHANNELS = {
    "CanalPlus.fr": {"id": "CanalPlus.fr", "name": "CANAL+"},
    "CanalPlusSport2.fr": {"id": "CanalPlusSport2.fr", "name": "CANAL+ SPORT 2"},
    "CanalPlusSport5.fr": {"id": "CanalPlusSport5.fr", "name": "CANAL+ SPORT 5"},
}


def events_of(*progs):
    return extract_sport_events(list(progs), CHANNELS)


# ───────────── normalisation des séances ─────────────

def test_motogp_race_without_affiche_is_accepted():
    p = prog("La course", "Grand Prix d'Australie", ["sport", "moto gp"], at(25, 3, 57), 49, "CanalPlus.fr")
    n = normalize_session_event(p)
    assert n["title"] == "Moto GP : Grand Prix d'Australie"
    assert n["subtitle"] == "Grand Prix d'Australie. La course."
    (e,) = events_of(p)
    assert e.sport == SportType.MOTOGP and e.competition == "Grand Prix d'Australie"


def test_moto2_moto3_labels_and_class_suffix():
    a = prog("Essais libres 2 des Moto 3", "Grand Prix d'Australie", ["sport", "moto 3"], at(23, 23, 35))
    b = prog("Essais Libres 1. Grand Prix de Malaisie", "Grand Prix de Malaisie", ["sport", "moto 2"], at(30, 2, 45))
    assert normalize_session_event(a)["title"] == "Moto 3 : Grand Prix d'Australie"
    assert normalize_session_event(a)["subtitle"] == "Grand Prix d'Australie. Essais libres 2."
    assert normalize_session_event(b)["title"] == "Moto 2 : Grand Prix de Malaisie"
    assert classify_sport(normalize_session_event(a)) == SportType.MOTOGP
    # catégorie seule (« moto 2 ») → MotoGP, pas F1
    assert classify_sport(prog("Essais", "Grand Prix de Malaisie", ["sport", "moto 2"], at(30, 7))) == SportType.MOTOGP


def test_f1_mexico_session_and_f1_academy_label():
    f1 = prog("Essais Libres 1", "Grand Prix du Mexique", ["sport", "formule 1"], at(30, 19, 15), 88)
    acad = prog("1re course", "Grand Prix des Etats-Unis", ["sport", "sport mecanique"], at(24, 0, 45), 45)
    assert normalize_session_event(f1)["title"] == "Formule 1 : Grand Prix du Mexique"
    n = normalize_session_event(acad)
    assert n["title"] == "F1 Academy : Grand Prix des États-Unis"
    assert classify_sport(n) == SportType.F1


def test_magazines_and_shows_are_not_sessions():
    for title, sub in [("La grille Moto", "Grand Prix d'Australie"), ("Moto : Le podium", "Grand Prix d'Australie"),
                       ("Débrief Moto", "Grand Prix de Malaisie"), ("Plateau sports mécaniques", "Formule 1 : Grand Prix des Etats-Unis"),
                       ("Fractionné F1", "Grand Prix de France historique 2026"), ("Parade des pilotes", "Grand Prix d'Australie")]:
        assert normalize_session_event(prog(title, sub, ["sport", "mag sports mecaniques"], at(25, 5))) is None, title


def test_tennis_and_golf_rounds():
    t = prog("Quart de finale. 1re partie", "Tournois ATP de Vienne et Bâle", ["sport", "tennis"], at(30, 14, 31), 285, "CanalPlusSport5.fr")
    g = prog("2e tour", "Championnat des Bermudes", ["sport", "golf"], at(23, 21, 0), 100)
    nt, ng = normalize_session_event(t), normalize_session_event(g)
    assert nt["title"] == "Tennis : Tournois ATP de Vienne et Bâle"
    assert nt["subtitle"].startswith("Tournois ATP de Vienne et Bâle. Quart de finale")
    assert ng["title"] == "Golf : Championnat des Bermudes" and ng["subtitle"] == "Championnat des Bermudes. 2e tour."
    (e,) = events_of(g)
    assert e.sport == SportType.GOLF and e.competition == "Championnat des Bermudes"


def test_padel_semifinal_title_uses_category():
    p = prog("1re demi-finale dames", "Koweït P1", ["sport", "padel"], at(30, 12), 120)
    n = normalize_session_event(p)
    assert n["title"] == "Padel : Koweït P1" and n["subtitle"] == "Koweït P1. 1re demi-finale dames."


def test_reviews_and_highlights_are_rejected():
    assert normalize_session_event(prog("Rallye : WRC, Rallye Italie Sardaigne", "Rallye Italie Sardaigne. Review.", ["sport"], at(29, 23))) is None
    assert normalize_session_event(prog("Endurance : 6 Heures de Barcelone", "6 Heures de Barcelone. Les meilleurs moments.", ["sport"], at(23, 4))) is None
    assert normalize_session_event(prog("Golf+, le mag", "Emission du 26 oct. 2026", ["sport", "golf"], at(27, 0))) is None


def test_table_tennis_is_not_tennis():
    p = prog("Tennis de table : WTT Champions de Montpellier", "WTT Champions de Montpellier.", ["sport"], at(28, 12), 300, "CanalPlus.fr")
    assert classify_sport(p) == SportType.OTHER


# ───────────── rediffusions de ces épreuves ─────────────

def ev_from(p):
    (e,) = events_of(p)
    return e


def test_motogp_session_replays_with_other_labels_are_dropped():
    live = ev_from(prog("La course", "Grand Prix d'Australie", ["sport", "moto gp"], at(25, 3, 57), 49, "CanalPlus.fr"))
    r1 = ev_from(prog("La course", "Grand Prix d'Australie", ["sport", "moto gp"], at(25, 14, 18), 36, "CanalPlus.fr"))
    r2 = ev_from(prog("La course des Moto GP", "Grand Prix d'Australie", ["sport", "moto gp"], at(28, 9, 5), 60, "CanalPlusSport2.fr"))
    moto3 = ev_from(prog("La course", "Grand Prix d'Australie", ["sport", "moto 3"], at(25, 1, 55), 45, "CanalPlusSport2.fr"))
    out, _ = refine_events([live, r1, r2, moto3], now=NOW)
    kept = {(e.title, e.start.strftime("%d %H:%M")) for e in out}
    assert kept == {("Moto GP : Grand Prix d'Australie", "25 03:57"), ("Moto 3 : Grand Prix d'Australie", "25 01:55")}, kept


def test_golf_round_replays_dropped_but_each_round_kept():
    mk = lambda rnd, d, h: ev_from(prog(rnd, "Grand Final. HotelPlanner Tour", ["sport", "golf"], at(d, h), 120))
    evs = [mk("1er tour", 29, 12), mk("1er tour", 30, 0), mk("1er tour", 30, 6), mk("2e tour", 30, 12), mk("2e tour", 31, 0)]
    out, _ = refine_events(evs, now=at(29, 8))
    assert [(e.subtitle, e.start.day, e.start.hour) for e in out] == [
        ("Grand Final. HotelPlanner Tour. 1er tour.", 29, 12), ("Grand Final. HotelPlanner Tour. 2e tour.", 30, 12)]


def test_padel_simulcast_kept_replay_dropped():
    mk = lambda ch, d, h: ev_from(prog("Finale dames", "Koweït P1", ["sport", "padel"], at(d, h), 90, ch))
    evs = [mk("CanalPlusSport2.fr", 31, 14), mk("CanalPlus.fr", 31, 14), mk("CanalPlusSport2.fr", 1, 9, ) if False else
           ev_from(prog("Finale dames", "Koweït P1", ["sport", "padel"], at(1, 9, month=11), 90))]
    out, _ = refine_events(evs, now=at(30, 8))
    assert len(out) == 2 and {e.start.day for e in out} == {31}


def test_tennis_overnight_replay_dropped_daytime_blocks_kept():
    mk = lambda d, h, ch="CanalPlusSport5.fr": ev_from(prog("2e tour", "Tournois ATP de Vienne et Bâle", ["sport", "tennis"], at(d, h, 1), 285, ch))
    evs = [mk(27, 18), mk(28, 2), mk(28, 8)]
    out, _ = refine_events(evs, now=at(26, 8))
    assert [(e.start.day, e.start.hour) for e in out] == [(27, 18)]
    # blocs successifs d'une même journée sur Eurosport : tous gardés
    blocks = [ev_from(prog("Quart de finale", "Masters 1000 de Shanghai", ["sport", "tennis"], at(30, h, 30), 60, "Eurosport1.fr")) for h in (7, 8, 10, 12, 14)]
    out2, _ = refine_events(blocks, now=at(29, 8))
    assert len(out2) == 5


def basket(t1, t2, start, sub=None, ch="beIN SPORTS 1"):
    global _n
    _n += 1
    return SportEvent(
        id=f"b{_n}", sport=SportType.BASKET, title=f"Basket-ball : Euroligue masculine | {t1} / {t2}",
        subtitle=sub, competition="Euroligue masculine",
        team1=Entity(name=t1, type="club"), team2=Entity(name=t2, type="club"),
        channel=Channel(id=f"{ch}.fr", name=ch, slug=ch.lower().replace(" ", "-").replace("sports", "").strip("-")),
        start=start, end=start + timedelta(minutes=120),
    )


def test_euroleague_repeat_drops_when_round_missing_on_first_airing():
    live = basket("BC Dubai", "Paris Basketball", at(27, 16, 45))
    replay = basket("BC Dubai", "Paris Basketball", at(28, 13, 30), "Euroligue masculine. 8e journée.")
    other = basket("ASVEL Lyon-Villeurbanne", "Caja Laboral Baskonia", at(30, 19, 45), "Euroligue masculine. 9e journée.")
    out, stats = refine_events([live, replay, other], now=NOW)
    assert [e.id for e in out] == [live.id, other.id] and stats["drop_replay_wave"] == 1


def test_euroleague_two_explicit_rounds_are_kept():
    a = basket("Real Madrid", "Olympiacos", at(27, 20, 30), "Euroligue masculine. 8e journée.")
    b = basket("Real Madrid", "Olympiacos", at(30, 20, 30), "Euroligue masculine. 9e journée.")
    out, _ = refine_events([a, b], now=NOW)
    assert len(out) == 2


# ───────────── ESPN : tentatives et bilan ─────────────

def test_espn_retries_on_403_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] <= 2:
            return httpx.Response(403, text="Access Denied")
        return httpx.Response(200, json={"events": []})

    async def go():
        old = fixtures.ESPN_BACKOFF, fixtures.ESPN_SPACING
        fixtures.ESPN_BACKOFF, fixtures.ESPN_SPACING = 0.001, 0
        try:
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
                return await fixtures._get_json(c, asyncio.Semaphore(1), "https://x.test/a", {})
        finally:
            fixtures.ESPN_BACKOFF, fixtures.ESPN_SPACING = old

    assert asyncio.run(go()) == {"events": []} and calls["n"] == 3


def test_espn_failures_are_counted_not_silent():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Access Denied")

    async def go():
        old = fixtures.ESPN_BACKOFF, fixtures.ESPN_SPACING, fixtures.ESPN_RETRIES
        fixtures.ESPN_BACKOFF, fixtures.ESPN_SPACING, fixtures.ESPN_RETRIES = 0.001, 0, 1
        real = httpx.AsyncClient
        try:
            httpx.AsyncClient = lambda **kw: real(transport=httpx.MockTransport(handler), **kw)
            await fixtures.fetch_fixtures(date(2026, 10, 25), date(2026, 10, 26), [("soccer", "fra.1")])
        finally:
            httpx.AsyncClient = real
            fixtures.ESPN_BACKOFF, fixtures.ESPN_SPACING, fixtures.ESPN_RETRIES = old

    asyncio.run(go())
    st = fixtures.LAST_FETCH_STATS["fixtures"]
    assert st["total"] == 2 and st["ok"] == 0 and len(st["failed"]) == 2


def test_f1_replays_dropped_without_espn_even_with_different_labels():
    # ESPN injoignable (403) : la 1re diffusion du flux est le direct, quels que soient les libellés
    mk = lambda t, sub, d, h, m=0, ch="CanalPlus.fr", cats=("sport", "formule 1"): ev_from(
        prog(t, sub, list(cats), at(d, h, m), 100, ch))
    evs = [
        mk("Essais qualificatifs", "Grand Prix des Etats-Unis", 24, 22, 38),
        mk("Essais qualificatifs", "Grand Prix des Etats-Unis", 25, 18, 35, "CanalPlusSport5.fr"),
        mk("Formule 1 : Grand Prix des Etats-Unis", "Grand Prix des Etats-Unis. Essais qualificatifs. Championnat du monde.", 29, 9, 57),
        mk("La course", "Grand Prix des Etats-Unis", 25, 20, 59),
        mk("La course", "Grand Prix des Etats-Unis", 25, 21, 0, "CanalPlusSport5.fr"),
        mk("La course", "Grand Prix des Etats-Unis", 25, 23, 19),
        mk("Formule 1 : Grand Prix des Etats-Unis", "Grand Prix des Etats-Unis. La course. Championnat du monde.", 29, 9, 57),
        mk("Feature Race", "Grand Prix des Etats-Unis", 25, 17, 55, cats=("sport", "sport mecanique")),
        mk("Feature Race", "Grand Prix des Etats-Unis", 25, 19, 17, cats=("sport", "sport mecanique")),
    ]
    out, _ = refine_events(evs, now=at(25, 12))
    got = sorted((e.title, e.start.day, e.start.hour, e.start.minute) for e in out)
    assert got == [
        ("F1 Academy : Grand Prix des États-Unis", 25, 17, 55),
        ("Formule 1 : Grand Prix des États-Unis", 24, 22, 38),
        ("Formule 1 : Grand Prix des États-Unis", 25, 20, 59),
        ("Formule 1 : Grand Prix des États-Unis", 25, 21, 0),
    ], got


def test_only_dot_fr_feeds_are_french():
    # Canal+ Sport 1-5 sont des feeds .af (Canal+ International) : la Liga y passe, pas en France.
    chans = {"CanalPlusSport1.af": {"id": "CanalPlusSport1.af", "name": "Canal+ Sport 1"},
             "CanalPlusSport.fr": {"id": "CanalPlusSport.fr", "name": "Canal+ Sport"},
             "CanalPlusSport.ch": {"id": "CanalPlusSport.ch", "name": "Canal+ Sport"},
             "DAZN.fr": {"id": "DAZN.fr", "name": "DAZN 1"}}
    mk = lambda cid, title, sub: {"channel_id": cid, "title": title, "subtitle": sub, "description": "",
                                  "categories": ["sport"], "start": at(25, 20, 55), "end": at(25, 23, 0)}
    progs = [mk("CanalPlusSport1.af", "FC Barcelone / Real Madrid", "Liga - 10e journée"),
             mk("CanalPlusSport1.af", "Lille / Lens", "Ligue 1 McDonald's - 9e journée"),
             mk("CanalPlusSport.ch", "Lille / Lens", "Ligue 1 McDonald's - 9e journée"),
             mk("DAZN.fr", "FC Barcelone / Real Madrid", "Football. Liga 10e journée.")]
    out = extract_sport_events(progs, chans, french_only=True)
    assert [(e.channel.slug, e.title) for e in out] == [("dazn-1", "FC Barcelone / Real Madrid")]


def run():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failed += 1
            import traceback
            print(f"  FAIL {name}: {exc!r}")
            traceback.print_exc(limit=3)
    print(f"  RESULTS: {len(tests) - failed}/{len(tests)} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
