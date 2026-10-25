/**
 * mergeEvents — un match = une carte.
 *
 * Le même match est souvent diffusé sur plusieurs chaînes (ex. Lens–Paris FC
 * sur Ligue 1+ et Canal+ Sport). On les regroupe en un seul événement dont
 * `channels` liste toutes les chaînes ; `channel` reste la première.
 */
import { Channel, SportEvent } from "../types";
import { kickoffOf } from "../constants";

const norm = (s?: string | null) =>
  (s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]/g, "");

function keyOf(e: SportEvent): string {
  if (e.team1 && e.team2) {
    const pair = [norm(e.team1.name), norm(e.team2.name)].sort().join("|");
    return `m:${e.sport}:${pair}`;
  }
  return `t:${e.sport}:${norm(e.title)}`;
}

const MATCH_TOLERANCE_MS = 45 * 60 * 1000;
const OTHER_TOLERANCE_MS = 10 * 60 * 1000;

export function mergeDuplicateEvents(events: SportEvent[]): SportEvent[] {
  const sorted = [...events].sort((a, b) => Date.parse(kickoffOf(a)) - Date.parse(kickoffOf(b)));
  const out: SportEvent[] = [];
  const index = new Map<string, number[]>();

  for (const e of sorted) {
    const key = keyOf(e);
    const t = Date.parse(kickoffOf(e));
    const tol = e.team1 && e.team2 ? MATCH_TOLERANCE_MS : OTHER_TOLERANCE_MS;

    const candidates = index.get(key) ?? [];
    const hit = candidates.find(i => Math.abs(Date.parse(kickoffOf(out[i])) - t) <= tol);

    if (hit === undefined) {
      out.push({ ...e, channels: [e.channel] });
      index.set(key, [...candidates, out.length - 1]);
      continue;
    }

    const merged = out[hit];
    const list: Channel[] = merged.channels ?? [merged.channel];
    const name = e.channel.name.toLowerCase();
    if (!list.some(c => c.name.toLowerCase() === name)) list.push(e.channel);
    merged.channels = list;
    if (e.status === "live") merged.status = "live";
    // id stable : le plus petit des ids fusionnés, quel que soit l'ordre des chaînes
    // (sinon une alerte posée sur la carte « Canal+ » se perd si l'ordre change)
    if (e.id < merged.id) merged.id = e.id;
  }

  return out;
}
