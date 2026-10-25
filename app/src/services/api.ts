/**
 * SportZap — API Service (Static CDN)
 *
 * Fetches sport events from a static JSON file hosted on GitHub Pages.
 * Updated every 4h by a GitHub Action.
 *
 * All filtering (sport, channel, day) is done client-side.
 * The app caches the full JSON locally with a 30-min TTL (mémoire et disque).
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import { DaySchedule, SportEvent, SportType } from "../types";
import { todayParisISO } from "../constants";

const CDN_BASE = "https://chaouky.github.io/sportzap";

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

// Cache mémoire avec date d'expiration : une app laissée ouverte doit se mettre à jour.
let _memoryCache: FullSchedule | null = null;
let _memoryAt = 0;

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
  if (!forceRefresh && _memoryCache && Date.now() - _memoryAt < CACHE_TTL) return _memoryCache;

  if (!forceRefresh) {
    const cached = await loadCache();
    if (cached && Date.now() - cached.fetchedAt < CACHE_TTL) {
      _memoryCache = cached.data;
      _memoryAt = cached.fetchedAt;
      return cached.data;
    }
  }

  try {
    const resp = await fetch(`${CDN_BASE}/events.json`);
    if (!resp.ok) throw new Error(`CDN ${resp.status}`);
    const data: FullSchedule = await resp.json();
    _memoryCache = data;
    _memoryAt = Date.now();
    await saveCache(data);
    return data;
  } catch (err) {
    // Hors ligne ou CDN en panne : on garde ce qu'on a (la fraîcheur est signalée par l'écran).
    if (_memoryCache) return _memoryCache;
    const stale = await loadCache();
    if (stale) { _memoryCache = stale.data; _memoryAt = stale.fetchedAt; return stale.data; }
    throw err;
  }
}

/**
 * Durée maximale plausible d'un direct, comptée depuis le coup d'envoi (minutes).
 * L'antenne continue souvent après le coup de sifflet final (débrief, plateau) :
 * sans ce plafond, un match fini reste « EN DIRECT » jusqu'à la fin de l'émission.
 */
const MAX_LIVE_MIN: Record<string, number> = {
  football: 135,   // 90 + mi-temps + arrêts de jeu (prolongations rares)
  rugby: 120,
  handball: 110,
  basket: 165,     // NBA ≈ 2h30
  volleyball: 140,
  foot_us: 215,    // NFL ≈ 3h20
};

function computeStatus(
  start: string, end: string | null, now: Date, sport?: string,
): "upcoming" | "live" | "finished" {
  const s = new Date(start);
  const e = end ? new Date(end) : null;
  if (e && now > e) return "finished";
  if (now >= s) {
    const cap = sport ? MAX_LIVE_MIN[sport] : undefined;
    if (cap && now.getTime() > s.getTime() + cap * 60_000) return "finished";
    return "live";
  }
  return "upcoming";
}

/** Jour calendaire précédent / suivant d'une date YYYY-MM-DD (sans effet de fuseau). */
export function shiftISO(iso: string, days: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().split("T")[0];
}

function withStatus(events: SportEvent[], now: Date): SportEvent[] {
  return events.map(e => ({ ...e, status: computeStatus(e.kickoff || e.start, e.end, now, e.sport) }));
}

export async function fetchEvents(options?: {
  date?: string; sport?: SportType; channel?: string; freeOnly?: boolean;
}): Promise<DaySchedule> {
  const schedule = await getFullSchedule();
  const targetDate = options?.date || todayParisISO();
  const now = new Date();
  const dayData = schedule.days.find(d => d.date === targetDate);
  let events = dayData?.events || [];

  // Les jours sont rangés par coup d'envoi : un match commencé la veille avant minuit
  // (NHL, NBA, F1…) est encore « en direct » aujourd'hui, on le garde dans la liste.
  if (targetDate === todayParisISO()) {
    const prev = schedule.days.find(d => d.date === shiftISO(targetDate, -1));
    const carried = (prev?.events || []).filter(
      e => computeStatus(e.kickoff || e.start, e.end, now, e.sport) === "live",
    );
    events = [...carried, ...events];
  }

  if (options?.sport) events = events.filter(e => e.sport === options.sport);
  if (options?.channel) events = events.filter(e => e.channel.slug === options.channel);
  if (options?.freeOnly) events = events.filter(e => e.channel.is_free);

  events = withStatus(events, now);
  events.sort((a, b) => {
    const ord = { live: 0, upcoming: 1, finished: 2 };
    return (ord[a.status] ?? 1) - (ord[b.status] ?? 1)
      || (a.kickoff || a.start).localeCompare(b.kickoff || b.start);
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

/** Date de génération du programme publié (pour signaler des données périmées). */
export async function fetchGeneratedAt(): Promise<string | null> {
  try {
    return (await getFullSchedule()).meta.generated_at || null;
  } catch { return null; }
}

/** Force un nouveau téléchargement (tirer pour rafraîchir). */
export async function forceRefresh() { await getFullSchedule(true); }

export async function fetchAllEvents(): Promise<SportEvent[]> {
  const s = await getFullSchedule();
  return s.days.flatMap(d => d.events);
}

/** Tous les événements à venir ou en cours, tous jours confondus (recherche). */
export async function fetchUpcomingEvents(): Promise<SportEvent[]> {
  const all = await fetchAllEvents();
  return withStatus(all, new Date()).filter(e => e.status !== "finished");
}
