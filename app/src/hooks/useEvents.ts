/**
 * SportZap — useEvents hook
 *
 * Charge le programme du jour, filtre (chaînes choisies, terminés),
 * regroupe les doublons (un match = une carte) puis groupe par tranche horaire.
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import { DaySchedule, SportEvent, SportType, TimeBlock } from "../types";
import { fetchEvents } from "../services/api";
import { mergeDuplicateEvents } from "../services/mergeEvents";
import { kickoffOf, parisHour } from "../constants";

const TIME_BLOCK_ORDER: TimeBlock[] = ["EN DIRECT", "MATIN", "APRÈS-MIDI", "SOIRÉE"];

function getTimeBlock(event: SportEvent): TimeBlock {
  if (event.status === "live") return "EN DIRECT";
  const hour = parisHour(kickoffOf(event));
  if (hour < 12) return "MATIN";
  if (hour < 18) return "APRÈS-MIDI";
  return "SOIRÉE";
}

export interface EventGroup {
  block: TimeBlock;
  events: SportEvent[];
}

export function useEvents(options?: {
  date?: string;
  sport?: SportType | "all";
  channel?: string;
  freeOnly?: boolean;
  channelSlugs?: Set<string>; // "Mes Chaînes"
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
      setError("Impossible de charger le programme.");
    } finally {
      setLoading(false);
    }
  }, [options?.date, options?.sport, options?.channel, options?.freeOnly]);

  useEffect(() => {
    load();
  }, [load]);

  const { groups, total, liveCount } = useMemo(() => {
    if (!schedule) return { groups: [] as EventGroup[], total: 0, liveCount: 0 };

    let filtered = schedule.events.filter(e => e.status !== "finished");
    if (options?.channelSlugs && options.channelSlugs.size > 0) {
      filtered = filtered.filter(e => options.channelSlugs!.has(e.channel.slug));
    }
    const merged = mergeDuplicateEvents(filtered);

    const map = new Map<TimeBlock, SportEvent[]>();
    for (const event of merged) {
      const block = getTimeBlock(event);
      if (!map.has(block)) map.set(block, []);
      map.get(block)!.push(event);
    }

    return {
      groups: TIME_BLOCK_ORDER
        .filter(block => map.has(block))
        .map(block => ({ block, events: map.get(block)! })),
      total: merged.length,
      liveCount: merged.filter(e => e.status === "live").length,
    };
  }, [schedule, options?.channelSlugs]);

  return {
    schedule,
    groups,
    loading,
    error,
    refresh: load,
    liveCount,
    eventCount: total,
  };
}
