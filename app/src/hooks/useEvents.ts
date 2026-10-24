/**
 * SportZap — useEvents hook
 *
 * Manages events state: fetching, filtering, grouping by time block.
 * Handles loading, error, and refresh states.
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import { DaySchedule, SportEvent, SportType, TimeBlock } from "../types";
import { fetchEvents } from "../services/api";

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
      console.warn("SportZap: impossible de charger le programme:", err);
      setSchedule(null);
      setError("Impossible de charger le programme. Tirez pour réessayer.");
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

    // Ne montrer que les matchs en cours ou à venir (pas les terminés)
    let filtered = schedule.events.filter(e => e.status !== "finished");
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
  }, [schedule, options?.channelSlugs]);

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
