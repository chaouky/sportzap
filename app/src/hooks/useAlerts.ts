/**
 * SportZap — useAlerts hook
 *
 * Manages match alert state:
 *  - Toggle alert for individual events (bell button)
 *  - Auto-schedule for favorites
 *  - Track which events have active alerts
 *  - Sync with Expo Notifications
 */
import { useState, useEffect, useCallback } from "react";
import {
  scheduleMatchAlert,
  cancelMatchAlert,
  getScheduledAlerts,
  autoScheduleFavoriteAlerts,
  configureNotifications,
  requestPermissions,
  ScheduledAlert,
} from "../services/notifications";
import { SportEvent } from "../types";

// L'écran Programme et la recherche utilisent chacun ce hook : sans état partagé,
// une alerte posée dans l'un n'apparaissait pas dans l'autre (cloche désynchronisée).
// L'état vit donc au niveau du module et chaque instance s'abonne aux changements.
let sharedAlerted: Set<string> = new Set();
let sharedPermission: boolean | null = null;
let initStarted = false;
const subscribers = new Set<() => void>();

function publish(next: Set<string>) {
  sharedAlerted = next;
  subscribers.forEach(fn => fn());
}

async function loadExisting() {
  const existing = await getScheduledAlerts();
  publish(new Set(existing.map(a => a.eventId)));
}

export function useAlerts() {
  const [, force] = useState(0);
  const alertedIds = sharedAlerted;
  const permissionGranted = sharedPermission;
  const setAlertedIds = useCallback((fn: (prev: Set<string>) => Set<string>) => {
    publish(fn(sharedAlerted));
  }, []);
  const setPermissionGranted = useCallback((v: boolean) => {
    sharedPermission = v;
    subscribers.forEach(f => f());
  }, []);

  // ── Init: configure + load existing (une seule fois pour toute l'app) ──
  useEffect(() => {
    const sub = () => force(n => n + 1);
    subscribers.add(sub);
    if (!initStarted) {
      initStarted = true;
      configureNotifications();
      loadExisting().catch(() => { initStarted = false; });
    }
    return () => { subscribers.delete(sub); };
  }, []);

  // ── Toggle alert for a single event ──
  const toggleAlert = useCallback(async (event: SportEvent) => {
    // Check permission on first toggle
    if (sharedPermission === null) {
      const granted = await requestPermissions();
      setPermissionGranted(granted);
      if (!granted) return;
    }

    const isActive = sharedAlerted.has(event.id);

    if (isActive) {
      // Cancel
      await cancelMatchAlert(event.id);
      setAlertedIds(prev => {
        const next = new Set(prev);
        next.delete(event.id);
        return next;
      });
    } else {
      // Schedule
      const sportEmoji: Record<string, string> = {
        football: "⚽", rugby: "🏉", tennis: "🎾", basket: "🏀",
        f1: "🏎", cyclisme: "🚴", mma: "🥊", handball: "🤾",
      };
      const emoji = sportEmoji[event.sport] || "🏅";
      const teams = event.team1 && event.team2
        ? `${event.team1.name} — ${event.team2.name}`
        : event.team1?.name || event.subtitle || "Match";

      const notifId = await scheduleMatchAlert({
        eventId: event.id,
        matchStart: event.kickoff || event.start,
        title: `${emoji} ${teams}`,
        subtitle: event.competition || event.sport,
        channel: event.channel.name,
      });

      if (notifId) {
        setAlertedIds(prev => {
          const next = new Set(prev);
          next.add(event.id);
          return next;
        });
      }
    }
  }, [setAlertedIds, setPermissionGranted]);

  // ── Auto-schedule for favorite matches ──
  const scheduleForFavorites = useCallback(async (
    events: SportEvent[],
    matchedIds: Set<string>,
  ) => {
    const count = await autoScheduleFavoriteAlerts(
      events.map(e => ({
        id: e.id,
        start: e.start,
        kickoff: e.kickoff,
        team1: e.team1 ? { name: e.team1.name } : null,
        team2: e.team2 ? { name: e.team2.name } : null,
        competition: e.competition,
        channel: { name: e.channel.name },
        sport: e.sport,
      })),
      matchedIds,
    );

    if (count > 0) await loadExisting();

    return count;
  }, []);

  return {
    alertedIds,
    isAlerted: (eventId: string) => sharedAlerted.has(eventId),
    toggleAlert,
    scheduleForFavorites,
    permissionGranted,
  };
}
