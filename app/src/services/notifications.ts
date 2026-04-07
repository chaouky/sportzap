/**
 * SportZap — Notification Service
 *
 * Handles:
 *  1. Permission request (iOS + Android)
 *  2. Scheduling local notifications X minutes before a match
 *  3. Cancelling notifications when user un-bells
 *  4. Auto-scheduling for favorites
 *  5. Badge management
 *
 * Uses Expo Notifications (local scheduling, no backend needed).
 * In production, add push tokens + server-side scheduling for
 * reliability when app is killed.
 */
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

const STORAGE_KEY = "@sportzap_notif_prefs";
const SCHEDULED_KEY = "@sportzap_scheduled_ids";

// ── Types ──

export interface NotifPrefs {
  enabled: boolean;
  minutesBefore: number;  // 5, 10, 15, 30, 60
  soundEnabled: boolean;
  favoriteAutoAlert: boolean; // auto-schedule for favorites
}

export interface ScheduledAlert {
  eventId: string;
  notifId: string;       // Expo notification identifier
  fireAt: string;        // ISO datetime
  title: string;
  body: string;
}

const DEFAULT_PREFS: NotifPrefs = {
  enabled: true,
  minutesBefore: 15,
  soundEnabled: true,
  favoriteAutoAlert: true,
};

// ── Configuration ──

/**
 * Configure notification handler (call once at app startup).
 * Determines how notifications appear when app is in foreground.
 */
export function configureNotifications() {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });

  // Android: create notification channel
  if (Platform.OS === "android") {
    Notifications.setNotificationChannelAsync("match-alerts", {
      name: "Alertes Match",
      description: "Rappels avant le début des matchs",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#6366F1",
      sound: "default",
    });
  }
}

// ── Permissions ──

/**
 * Request notification permissions.
 * Returns true if granted.
 */
export async function requestPermissions(): Promise<boolean> {
  if (!Device.isDevice) {
    console.warn("Push notifications require a physical device");
    return false;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  if (existingStatus === "granted") return true;

  const { status } = await Notifications.requestPermissionsAsync();
  return status === "granted";
}

/**
 * Check if notifications are currently permitted.
 */
export async function checkPermissions(): Promise<boolean> {
  const { status } = await Notifications.getPermissionsAsync();
  return status === "granted";
}

// ── Preferences ──

export async function loadPrefs(): Promise<NotifPrefs> {
  try {
    const stored = await AsyncStorage.getItem(STORAGE_KEY);
    if (stored) return { ...DEFAULT_PREFS, ...JSON.parse(stored) };
  } catch (e) {
    console.warn("Failed to load notif prefs:", e);
  }
  return DEFAULT_PREFS;
}

export async function savePrefs(prefs: NotifPrefs): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch (e) {
    console.warn("Failed to save notif prefs:", e);
  }
}

// ── Scheduled alerts tracking ──

async function loadScheduled(): Promise<Record<string, ScheduledAlert>> {
  try {
    const stored = await AsyncStorage.getItem(SCHEDULED_KEY);
    if (stored) return JSON.parse(stored);
  } catch (e) {}
  return {};
}

async function saveScheduled(scheduled: Record<string, ScheduledAlert>): Promise<void> {
  try {
    await AsyncStorage.setItem(SCHEDULED_KEY, JSON.stringify(scheduled));
  } catch (e) {}
}

// ── Schedule / Cancel ──

/**
 * Schedule a notification for a sport event.
 *
 * @param eventId - Unique event ID from the API
 * @param matchStart - ISO datetime string of match start
 * @param title - e.g. "⚽ PSG — OM"
 * @param subtitle - e.g. "Ligue 1 · J29"
 * @param channel - e.g. "DAZN 1"
 * @param minutesBefore - How many minutes before kickoff
 * @returns The notification identifier, or null if failed
 */
export async function scheduleMatchAlert(params: {
  eventId: string;
  matchStart: string;
  title: string;
  subtitle: string;
  channel: string;
  minutesBefore?: number;
}): Promise<string | null> {
  const prefs = await loadPrefs();
  if (!prefs.enabled) return null;

  const permitted = await checkPermissions();
  if (!permitted) {
    const granted = await requestPermissions();
    if (!granted) return null;
  }

  const mins = params.minutesBefore ?? prefs.minutesBefore;
  const matchTime = new Date(params.matchStart);
  const fireAt = new Date(matchTime.getTime() - mins * 60 * 1000);

  // Don't schedule if already in the past
  if (fireAt.getTime() <= Date.now()) {
    return null;
  }

  // Cancel existing alert for this event if any
  await cancelMatchAlert(params.eventId);

  const body = mins === 0
    ? `C'est parti ! ${params.subtitle} sur ${params.channel}`
    : `Dans ${mins} min sur ${params.channel} — ${params.subtitle}`;

  try {
    const notifId = await Notifications.scheduleNotificationAsync({
      content: {
        title: params.title,
        body,
        sound: prefs.soundEnabled ? "default" : undefined,
        badge: 1,
        data: {
          eventId: params.eventId,
          type: "match-alert",
        },
        ...(Platform.OS === "android" && {
          channelId: "match-alerts",
        }),
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.DATE,
        date: fireAt,
      },
    });

    // Track scheduled alert
    const scheduled = await loadScheduled();
    scheduled[params.eventId] = {
      eventId: params.eventId,
      notifId,
      fireAt: fireAt.toISOString(),
      title: params.title,
      body,
    };
    await saveScheduled(scheduled);

    return notifId;
  } catch (e) {
    console.error("Failed to schedule notification:", e);
    return null;
  }
}

/**
 * Cancel a scheduled notification for an event.
 */
export async function cancelMatchAlert(eventId: string): Promise<void> {
  const scheduled = await loadScheduled();
  const existing = scheduled[eventId];

  if (existing) {
    try {
      await Notifications.cancelScheduledNotificationAsync(existing.notifId);
    } catch (e) {
      // Already fired or cancelled
    }
    delete scheduled[eventId];
    await saveScheduled(scheduled);
  }
}

/**
 * Check if an event has a scheduled alert.
 */
export async function isAlertScheduled(eventId: string): Promise<boolean> {
  const scheduled = await loadScheduled();
  return eventId in scheduled;
}

/**
 * Get all currently scheduled alerts.
 */
export async function getScheduledAlerts(): Promise<ScheduledAlert[]> {
  const scheduled = await loadScheduled();
  return Object.values(scheduled);
}

/**
 * Cancel all scheduled alerts.
 */
export async function cancelAllAlerts(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
  await saveScheduled({});
}

// ── Bulk scheduling for favorites ──

/**
 * Auto-schedule alerts for events matching user's favorites.
 * Called after each data refresh.
 *
 * @param events - All upcoming events
 * @param matchedEventIds - Event IDs that match user's favorites
 */
export async function autoScheduleFavoriteAlerts(
  events: Array<{
    id: string;
    start: string;
    team1?: { name: string } | null;
    team2?: { name: string } | null;
    competition?: string | null;
    channel: { name: string };
    sport: string;
  }>,
  matchedEventIds: Set<string>,
): Promise<number> {
  const prefs = await loadPrefs();
  if (!prefs.enabled || !prefs.favoriteAutoAlert) return 0;

  let count = 0;
  const sportEmoji: Record<string, string> = {
    football: "⚽", rugby: "🏉", tennis: "🎾", basket: "🏀",
    f1: "🏎", cyclisme: "🚴", mma: "🥊", handball: "🤾",
  };

  for (const event of events) {
    if (!matchedEventIds.has(event.id)) continue;

    // Build notification text
    const emoji = sportEmoji[event.sport] || "🏅";
    const teams = event.team1 && event.team2
      ? `${event.team1.name} — ${event.team2.name}`
      : event.team1?.name || "Événement sport";

    const result = await scheduleMatchAlert({
      eventId: event.id,
      matchStart: event.start,
      title: `${emoji} ${teams}`,
      subtitle: event.competition || event.sport,
      channel: event.channel.name,
    });

    if (result) count++;
  }

  return count;
}

// ── Notification response handler ──

/**
 * Register a handler for when user taps a notification.
 * Returns a cleanup function.
 */
export function onNotificationTap(
  callback: (eventId: string) => void,
): () => void {
  const subscription = Notifications.addNotificationResponseReceivedListener(
    (response) => {
      const data = response.notification.request.content.data;
      if (data?.eventId && data?.type === "match-alert") {
        callback(data.eventId as string);
      }
    },
  );

  return () => subscription.remove();
}
