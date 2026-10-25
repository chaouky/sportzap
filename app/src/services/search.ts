/**
 * search — recherche texte dans le programme (équipes, compétition, sport, chaîne…).
 * Insensible à la casse et aux accents ; tous les mots saisis doivent être trouvés.
 */
import { SportEvent } from "../types";
import { kickoffOf } from "../constants";
import { describeEvent } from "./describeEvent";

export const norm = (s?: string | null) =>
  (s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

function haystack(e: SportEvent): string {
  const info = describeEvent(e);
  const channels = (e.channels && e.channels.length ? e.channels : [e.channel]).map(c => c.name);
  return norm([
    e.team1?.name, e.team1?.short, e.team2?.name, e.team2?.short,
    e.title, e.subtitle, e.competition, info.sportLabel, info.context, info.headline,
    ...channels,
  ].filter(Boolean).join(" "));
}

export function searchEvents(events: SportEvent[], query: string, limit = 80): SportEvent[] {
  const words = norm(query).split(" ").filter(w => w.length > 0);
  if (words.length === 0) return [];
  const out: SportEvent[] = [];
  for (const e of events) {
    const h = haystack(e);
    if (words.every(w => h.includes(w))) out.push(e);
  }
  out.sort((a, b) => Date.parse(kickoffOf(a)) - Date.parse(kickoffOf(b)));
  return out.slice(0, limit);
}
