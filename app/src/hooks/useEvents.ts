/**
 * SportZap — useEvents hook
 *
 * Manages events state: fetching, filtering, grouping by time block.
 * Handles loading, error, and refresh states.
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import { DaySchedule, SportEvent, SportType, TimeBlock } from "../types";
import { fetchEvents } from "../services/api";

// ── Offline mock data (used when API unreachable) ──
const MOCK_EVENTS: SportEvent[] = [
  {
    id: "mock1", sport: "football", competition: "Ligue 1 · J29",
    title: "Football : Ligue 1", subtitle: "PSG / OM",
    team1: { name: "Paris-SG", type: "club" },
    team2: { name: "Olympique de Marseille", type: "club" },
    channel: { id: "dazn", name: "DAZN 1", slug: "dazn-1", is_free: false },
    start: new Date().toISOString(), end: new Date().toISOString(),
    status: "live", score1: 2, score2: 1, minute: "67'",
  },
  {
    id: "mock2", sport: "tennis", competition: "Miami Open · Finale",
    title: "Tennis : Masters 1000", subtitle: "Djokovic / Alcaraz",
    team1: { name: "N. Djokovic", type: "player", country_code: "rs" },
    team2: { name: "C. Alcaraz", type: "player", country_code: "es" },
    channel: { id: "es1", name: "Eurosport 1", slug: "eurosport-1", is_free: false },
    start: new Date().toISOString(), end: new Date().toISOString(),
    status: "upcoming",
  },
  {
    id: "mock3", sport: "handball", competition: "Golden League",
    title: "Handball : Golden League", subtitle: "France / Danemark",
    team1: { name: "France", type: "country", country_code: "fr" },
    team2: { name: "Danemark", type: "country", country_code: "dk" },
    channel: { id: "f2", name: "France 2", slug: "france-2", is_free: true },
    start: new Date().toISOString(), end: new Date().toISOString(),
    status: "upcoming",
  },
];

// ── Time block grouping ──
const TIME_BLOCK_ORDER: TimeBlock[] = ["EN DIRECT", "MATIN", "APRÈS-MIDI", "SOIRÉE"];

function getTimeBlock(event: SportEvent): TimeBlock {
  if (event.status === "live") return "EN DIRECT";
  const hour = new Date(event.start).getHours();
  if (hour < 12) return "MATIN";
  if (hour < 18) return "APRÈS-MIDI";
  return "SOIRÉE";
}

export interface EventGroup {
  block: TimeBlock;
  events: SportEvent[];
}

// ── Hook ──

export function useEvents(options?: {
  date?: string;
  sport?: SportType | "all";
  channel?: string;
  freeOnly?: boolean;
  channelSlugs?: Set<string>; // "Mes Chaînes" filter
}) {
  const [schedule, setSchedule] = useState<DaySchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const sportFilter = options?.sport === "all" ? undefined : options?.sport;
      const data = await fetchEvents({
        date: options?.date,
        sport: sportFilter as SportType | undefined,
        channel: options?.channel,
        freeOnly: options?.freeOnly,
      });
      setSchedule(data);
    } catch (err) {
      console.warn("API unavailable, using mock data:", err);
      setError("Mode hors-ligne");
      // Fallback to mock
      setSchedule({
        date: options?.date || new Date().toISOString().split("T")[0],
        event_count: MOCK_EVENTS.length,
        live_count: MOCK_EVENTS.filter(e => e.status === "live").length,
        events: MOCK_EVENTS,
      });
    } finally {
      setLoading(false);
    }
  }, [options?.date, options?.sport, options?.channel, options?.freeOnly]);

  useEffect(() => {
    load();
  }, [load]);

  // Group events by time block (after channel filter)
  const groups: EventGroup[] = useMemo(() => {
    if (!schedule) return [];

    // Apply "Mes Chaînes" filter client-side
    let filtered = schedule.events;
    if (options?.channelSlugs && options.channelSlugs.size > 0) {
      filtered = filtered.filter(e => options.channelSlugs!.has(e.channel.slug));
    }

    const map = new Map<TimeBlock, SportEvent[]>();
    for (const event of filtered) {
      const block = getTimeBlock(event);
      if (!map.has(block)) map.set(block, []);
      map.get(block)!.push(event);
    }

    return TIME_BLOCK_ORDER
      .filter(block => map.has(block))
      .map(block => ({ block, events: map.get(block)! }));
  }, [schedule]);

  return {
    schedule,
    groups,
    loading,
    error,
    refresh: load,
    liveCount: schedule?.live_count ?? 0,
    eventCount: schedule?.event_count ?? 0,
  };
}
