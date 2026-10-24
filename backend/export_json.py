"""
SportZap — Static JSON Exporter

Télécharge le XMLTV, extrait les événements sportifs des 7 prochains jours
et génère un fichier events.json compatible avec l'app mobile.

Usage:
    python export_json.py                        # → ./output/events.json
    python export_json.py --days 5               # 5 jours au lieu de 7
    python export_json.py --sample               # utilise le sample XMLTV local
    python export_json.py --out /tmp/events.json # chemin custom

Output format (FullSchedule):
{
  "meta": {
    "generated_at": "2026-04-07T12:00:00Z",
    "total_events": 142,
    "total_days": 7,
    "sports": ["football", "tennis", ...],
    "channels": [{"slug": "tf1", "name": "TF1", "is_free": true}, ...]
  },
  "days": [
    {
      "date": "2026-04-07",
      "event_count": 18,
      "events": [...]
    },
    ...
  ]
}
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Ajoute le répertoire parent au path pour importer app/
sys.path.insert(0, str(Path(__file__).parent))

from app.fetcher import XMLTVFetcher
from app.fixtures import fetch_fixtures
from app.schedule_refine import PARIS, refine_events, streaming_fixtures
from app.sport_extractor import build_channel


def make_date_range(days: int) -> list[str]:
    # Les jours des événements sont en heure de Paris (offset du XMLTV)
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    return [(today + timedelta(days=i)).isoformat() for i in range(days)]


async def export(days: int = 7, sample: bool = False, out_path: str = "output/events.json",
                 use_espn: bool = True):
    fetcher = XMLTVFetcher(source="full", french_only=True)

    sample_file = Path(__file__).parent / "data" / "sample_xmltv.xml"

    if sample and sample_file.exists():
        print(f"[export] Utilisation du sample: {sample_file}")
        fetcher.parse(source_override=sample_file)
    else:
        print("[export] Téléchargement XMLTV depuis xmltvfr.fr...")
        await fetcher.refresh()

    print(f"[export] {fetcher.stats['cached_events']} événements chargés")

    # ── Coup d'envoi officiel + suppression des rediffusions ──
    fixtures = []
    if use_espn and not sample:
        today = datetime.now(PARIS).date()
        try:
            fixtures = await fetch_fixtures(today - timedelta(days=9), today + timedelta(days=days))
            print(f"[export] Calendrier officiel (ESPN): {len(fixtures)} rencontres")
        except Exception as exc:  # le calendrier est un bonus : on continue sans
            print(f"[export] ⚠ ESPN indisponible ({exc}) — coups d'envoi estimés")
    all_events, stats = refine_events(fetcher.get_events(), fixtures)
    extra = streaming_fixtures(all_events, fixtures)
    if extra:
        all_events = sorted(all_events + extra, key=lambda x: (x.kickoff or x.start, x.start))
        print(f"[export] {len(extra)} diffusions streaming ajoutées depuis le calendrier officiel")
    print(f"[export] Affinage: {stats.get('in', 0)} diffusions → {stats.get('out', 0)} "
          f"({stats.get('espn_matched', 0)} recalées sur l'horaire officiel)")
    print(f"[export]   détail: {stats}")

    def event_day(ev) -> str:
        return (ev.kickoff or ev.start).astimezone(PARIS).date().isoformat()

    date_range = make_date_range(days)
    all_days = []
    all_sports: set[str] = set()
    all_channels: dict[str, dict] = {}
    total_events = 0

    for date in date_range:
        events = [e for e in all_events if event_day(e) == date]
        if not events:
            continue

        events_data = []
        for e in events:
            all_sports.add(e.sport.value if hasattr(e.sport, "value") else e.sport)
            slug = e.channel.slug
            if slug not in all_channels:
                all_channels[slug] = {
                    "slug": slug,
                    "name": e.channel.name,
                    "is_free": e.channel.is_free,
                }

            # Sérialise en dict compatible JSON
            event_dict = e.model_dump() if hasattr(e, "model_dump") else e.dict()

            # Convertit les enums en strings
            def serialize(obj):
                if isinstance(obj, dict):
                    return {k: serialize(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [serialize(i) for i in obj]
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if hasattr(obj, "value"):
                    return obj.value
                return obj

            events_data.append(serialize(event_dict))

        all_days.append({
            "date": date,
            "event_count": len(events_data),
            "events": events_data,
        })
        total_events += len(events_data)
        print(f"[export]   {date}: {len(events_data)} événements")

    output = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events": total_events,
            "total_days": len(all_days),
            "sports": sorted(all_sports),
            "channels": list(all_channels.values()),
        },
        "days": all_days,
    }

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[export] ✓ {total_events} événements sur {len(all_days)} jours")
    print(f"[export] ✓ Fichier généré: {out_file.resolve()}")
    print(f"[export] ✓ Taille: {out_file.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SportZap JSON exporter")
    parser.add_argument("--days", type=int, default=7, help="Nombre de jours (défaut: 7)")
    parser.add_argument("--sample", action="store_true", help="Utiliser le sample XMLTV local")
    parser.add_argument("--out", type=str, default="output/events.json", help="Chemin de sortie")
    parser.add_argument("--no-espn", action="store_true", help="Ne pas interroger le calendrier ESPN")
    args = parser.parse_args()

    asyncio.run(export(days=args.days, sample=args.sample, out_path=args.out,
                       use_espn=not args.no_espn))
