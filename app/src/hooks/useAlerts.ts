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

export function useAlerts() {
  const [alertedIds, setAlertedIds] = useState<Set<string>>(new Set());
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);

  // ── Init: configure + load existing ──
  useEffect(() => {
    configureNotifications();

    (async () => {
      // Load existing scheduled alerts
      const existing = await getScheduledAlerts();
      setAlertedIds(new Set(existing.map(a => a.eventId)));
    })();
  }, []);

  // ── Toggle alert for a single event ──
  const toggleAlert = useCallback(async (event: SportEvent) => {
    // Check permission on first toggle
    if (permissionGranted === null) {
      const granted = await requestPermissions();
      setPermissionGranted(granted);
      if (!granted) return;
    }

    const isActive = alertedIds.has(event.id);

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
        matchStart: event.start,
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
  }, [alertedIds, permissionGranted]);

  // ── Auto-schedule for favorite matches ──
  const scheduleForFavorites = useCallback(async (
    events: SportEvent[],
    matchedIds: Set<string>,
  ) => {
    const count = await autoScheduleFavoriteAlerts(
      events.map(e => ({
        id: e.id,
        start: e.start,
        team1: e.team1 ? { name: e.team1.name } : null,
        team2: e.team2 ? { name: e.team2.name } : null,
        competition: e.competition,
        channel: { name: e.channel.name },
        sport: e.sport,
      })),
      matchedIds,
    );

    if (count > 0) {
      // Refresh alerted IDs
      const existing = await getScheduledAlerts();
      setAlertedIds(new Set(existing.map(a => a.eventId)));
    }

    return count;
  }, []);

  return {
    alertedIds,
    isAlerted: (eventId: string) => alertedIds.has(eventId),
    toggleAlert,
    scheduleForFavorites,
    permissionGranted,
  };
}
