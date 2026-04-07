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

# Ajoute le répertoire parent au path pour importer app/
sys.path.insert(0, str(Path(__file__).parent))

from app.fetcher import XMLTVFetcher
from app.sport_extractor import build_channel


def make_date_range(days: int) -> list[str]:
    today = datetime.now(timezone.utc).date()
    return [(today + timedelta(days=i)).isoformat() for i in range(days)]


async def export(days: int = 7, sample: bool = False, out_path: str = "output/events.json"):
    fetcher = XMLTVFetcher(source="full")

    sample_file = Path(__file__).parent / "data" / "sample_xmltv.xml"

    if sample and sample_file.exists():
        print(f"[export] Utilisation du sample: {sample_file}")
        fetcher.parse(source_override=sample_file)
    else:
        print("[export] Téléchargement XMLTV depuis xmltvfr.fr...")
        await fetcher.refresh()

    print(f"[export] {fetcher.stats['cached_events']} événements chargés")

    date_range = make_date_range(days)
    all_days = []
    all_sports: set[str] = set()
    all_channels: dict[str, dict] = {}
    total_events = 0

    for date in date_range:
        events = fetcher.get_events(date=date)
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
    args = parser.parse_args()

    asyncio.run(export(days=args.days, sample=args.sample, out_path=args.out))
