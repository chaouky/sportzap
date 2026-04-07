/**
 * SportZap — API Service (Static CDN)
 *
 * Fetches sport events from a static JSON file hosted on GitHub Pages.
 * Updated every 4h by a GitHub Action.
 *
 * All filtering (sport, channel, day) is done client-side.
 * The app caches the full JSON locally with a 30-min TTL.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import { DaySchedule, SportEvent, SportType } from "../types";

const CDN_BASE = __DEV__
  ? "http://localhost:8080"
  : "https://YOUR_USERNAME.github.io/sportzap-data";

const CACHE_KEY = "@sportzap_events_cache";
const CACHE_TTL = 30 * 60 * 1000;

interface CachedData { fetchedAt: number; data: FullSchedule; }

interface FullSchedule {
  meta: {
    generated_at: string;
    total_events: number;
    total_days: number;
    sports: string[];
    channels: Array<{ slug: string; name: string; is_free: boolean }>;
  };
  days: Array<{ date: string; event_count: number; events: SportEvent[] }>;
}

let _memoryCache: FullSchedule | null = null;

async function loadCache(): Promise<CachedData | null> {
  try {
    const raw = await AsyncStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

async function saveCache(data: FullSchedule): Promise<void> {
  try {
    await AsyncStorage.setItem(CACHE_KEY, JSON.stringify({ fetchedAt: Date.now(), data }));
  } catch {}
}

async function getFullSchedule(forceRefresh = false): Promise<FullSchedule> {
  if (_memoryCache && !forceRefresh) return _memoryCache;

  if (!forceRefresh) {
    const cached = await loadCache();
    if (cached && Date.now() - cached.fetchedAt < CACHE_TTL) {
      _memoryCache = cached.data;
      return cached.data;
    }
  }

  try {
    const resp = await fetch(`${CDN_BASE}/events.json`);
    if (!resp.ok) throw new Error(`CDN ${resp.status}`);
    const data: FullSchedule = await resp.json();
    _memoryCache = data;
    await saveCache(data);
    return data;
  } catch (err) {
    const stale = await loadCache();
    if (stale) { _memoryCache = stale.data; return stale.data; }
    throw err;
  }
}

function computeStatus(start: string, end: string | null, now: Date): "upcoming" | "live" | "finished" {
  const s = new Date(start);
  const e = end ? new Date(end) : null;
  if (e && now > e) return "finished";
  if (now >= s) return "live";
  return "upcoming";
}

export async function fetchEvents(options?: {
  date?: string; sport?: SportType; channel?: string; freeOnly?: boolean;
}): Promise<DaySchedule> {
  const schedule = await getFullSchedule();
  const targetDate = options?.date || new Date().toISOString().split("T")[0];
  const dayData = schedule.days.find(d => d.date === targetDate);
  let events = dayData?.events || [];

  if (options?.sport) events = events.filter(e => e.sport === options.sport);
  if (options?.channel) events = events.filter(e => e.channel.slug === options.channel);
  if (options?.freeOnly) events = events.filter(e => e.channel.is_free);

  const now = new Date();
  events = events.map(e => ({ ...e, status: computeStatus(e.start, e.end, now) }));
  events.sort((a, b) => {
    const ord = { live: 0, upcoming: 1, finished: 2 };
    return (ord[a.status] ?? 1) - (ord[b.status] ?? 1) || a.start.localeCompare(b.start);
  });

  return {
    date: targetDate,
    event_count: events.length,
    live_count: events.filter(e => e.status === "live").length,
    events,
  };
}

export async function fetchEvent(eventId: string): Promise<SportEvent | null> {
  const schedule = await getFullSchedule();
  for (const day of schedule.days) {
    const ev = day.events.find(e => e.id === eventId);
    if (ev) return ev;
  }
  return null;
}

export async function fetchChannels() {
  const s = await getFullSchedule();
  return { channels: s.meta.channels, total: s.meta.channels.length };
}

export async function fetchSports() {
  const s = await getFullSchedule();
  const counts: Record<string, number> = {};
  s.days.forEach(d => d.events.forEach(e => { counts[e.sport] = (counts[e.sport] || 0) + 1; }));
  return { sports: s.meta.sports.map(sp => ({ id: sp, label: sp.charAt(0).toUpperCase() + sp.slice(1), event_count: counts[sp] || 0 })) };
}

export async function healthCheck() {
  try {
    const s = await getFullSchedule();
    return { status: "ok", generated_at: s.meta.generated_at, total_events: s.meta.total_events };
  } catch { return { status: "offline", generated_at: "", total_events: 0 }; }
}

export async function forceRefresh() { await getFullSchedule(true); }

export async function fetchAllEvents(): Promise<SportEvent[]> {
  const s = await getFullSchedule();
  return s.days.flatMap(d => d.events);
}
