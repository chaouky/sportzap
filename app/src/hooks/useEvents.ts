/**
 * SportZap — useEvents hook
 *
 * Charge le programme du jour, filtre (chaînes choisies, terminés),
 * regroupe les doublons (un match = une carte) puis groupe par tranche horaire.
 *
 * Rafraîchissement : toutes les minutes (les statuts « en direct » / « terminé »
 * sont recalculés localement, le réseau n'est sollicité qu'à l'expiration du cache),
 * au retour au premier plan, et sur demande (tirer pour rafraîchir = réseau).
 */
import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { AppState } from "react-native";
import { DaySchedule, SportEvent, SportType, TimeBlock } from "../types";
import { fetchEvents, fetchGeneratedAt, forceRefresh } from "../services/api";
import { mergeDuplicateEvents } from "../services/mergeEvents";
import { kickoffOf, parisHour } from "../constants";

const TIME_BLOCK_ORDER: TimeBlock[] = ["EN DIRECT", "MATIN", "APRÈS-MIDI", "SOIRÉE"];
const TICK_MS = 60 * 1000;

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
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const seq = useRef(0); // ignore les réponses d'une requête devenue obsolète

  const load = useCallback(async (mode: "initial" | "silent" | "network" = "initial") => {
    const id = ++seq.current;
    if (mode !== "silent") {
      setLoading(true);
      setError(null);
    }

    try {
      if (mode === "network") await forceRefresh().catch(() => {});
      const sportFilter = options?.sport === "all" ? undefined : options?.sport;
      const data = await fetchEvents({
        date: options?.date,
        sport: sportFilter as SportType | undefined,
        channel: options?.channel,
        freeOnly: options?.freeOnly,
      });
      const gen = await fetchGeneratedAt();
      if (id !== seq.current) return;
      setSchedule(data);
      setGeneratedAt(gen);
      setError(null);
    } catch (err) {
      if (id !== seq.current) return;
      console.warn("SportZap: impossible de charger le programme:", err);
      if (mode !== "silent") {
        setSchedule(null);
        setError("Impossible de charger le programme.");
      }
    } finally {
      if (id === seq.current && mode !== "silent") setLoading(false);
    }
  }, [options?.date, options?.sport, options?.channel, options?.freeOnly]);

  useEffect(() => {
    load("initial");
  }, [load]);

  // Rafraîchissement automatique : minuteur + retour au premier plan
  useEffect(() => {
    const timer = setInterval(() => load("silent"), TICK_MS);
    const sub = AppState.addEventListener("change", state => {
      if (state === "active") load("silent");
    });
    return () => { clearInterval(timer); sub.remove(); };
  }, [load]);

  const refresh = useCallback(() => load("network"), [load]);

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
    refresh,
    generatedAt,
    liveCount,
    eventCount: total,
  };
}
