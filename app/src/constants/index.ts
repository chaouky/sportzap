import { SportFilter, DayOption } from "../types";

// ═══ SPORT FILTERS ═══
export const SPORTS: SportFilter[] = [
  { id: "all", label: "Tout", color: "#1A1A1A" },
  { id: "football", label: "Football", color: "#34D399" },
  { id: "rugby", label: "Rugby", color: "#F97316" },
  { id: "tennis", label: "Tennis", color: "#A3E635" },
  { id: "basket", label: "Basket", color: "#FB923C" },
  { id: "f1", label: "F1", color: "#EF4444" },
  { id: "cyclisme", label: "Cyclisme", color: "#FACC15" },
  { id: "mma", label: "MMA", color: "#C026D3" },
  { id: "handball", label: "Handball", color: "#38BDF8" },
  { id: "boxe", label: "Boxe", color: "#F43F5E" },
  { id: "volleyball", label: "Volley", color: "#8B5CF6" },
];

// ═══ CHANNEL BADGES ═══
// Visual config for channel pills
export const CHANNEL_BADGES: Record<string, { label: string; bg: string; fg: string }> = {
  "tf1":            { label: "TF1",  bg: "#0055A4", fg: "#fff" },
  "france-2":       { label: "F·2",  bg: "#E4003A", fg: "#fff" },
  "france-3":       { label: "F·3",  bg: "#0055A4", fg: "#fff" },
  "france-4":       { label: "F·4",  bg: "#6B21A8", fg: "#fff" },
  "france-5":       { label: "F·5",  bg: "#16A34A", fg: "#fff" },
  "canal-plus":     { label: "C+",   bg: "#1A1A1A", fg: "#fff" },
  "canal-plus-sport": { label: "C+S", bg: "#1A1A1A", fg: "#fff" },
  "canal-plus-foot":  { label: "C+F", bg: "#1A1A1A", fg: "#fff" },
  "bein-1":         { label: "beIN", bg: "#F7B500", fg: "#000" },
  "bein-2":         { label: "bN2",  bg: "#F7B500", fg: "#000" },
  "bein-3":         { label: "bN3",  bg: "#F7B500", fg: "#000" },
  "rmc-sport-1":    { label: "RMC",  bg: "#D40000", fg: "#fff" },
  "rmc-sport-2":    { label: "RMC2", bg: "#D40000", fg: "#fff" },
  "eurosport-1":    { label: "ES",   bg: "#003DA6", fg: "#fff" },
  "eurosport-2":    { label: "ES2",  bg: "#003DA6", fg: "#fff" },
  "lequipe":        { label: "LÉQ",  bg: "#FFD700", fg: "#000" },
  "dazn-1":         { label: "DAZN", bg: "#0C0C0E", fg: "#fff" },
  "dazn-2":         { label: "DZ2",  bg: "#0C0C0E", fg: "#fff" },
  "sport-en-france":{ label: "SEF",  bg: "#0074E4", fg: "#fff" },
  "infosport-plus": { label: "IS+",  bg: "#1A1A1A", fg: "#fff" },
  "m6":             { label: "M6",   bg: "#F59E0B", fg: "#000" },
};

// Fallback badge for unknown channels
export const DEFAULT_BADGE = { label: "TV", bg: "#6B7280", fg: "#fff" };

export function getChannelBadge(slug: string) {
  return CHANNEL_BADGES[slug] || DEFAULT_BADGE;
}

// ═══ COLORS ═══
export const COLORS = {
  bg: "#F5F2ED",
  card: "#FFFFFF",
  text: "#1A1A1A",
  textSecondary: "rgba(0,0,0,0.35)",
  textTertiary: "rgba(0,0,0,0.18)",
  border: "rgba(0,0,0,0.04)",
  borderActive: "rgba(0,0,0,0.08)",
  live: "#EF4444",
  liveBg: "rgba(239,68,68,0.03)",
  liveBorder: "rgba(239,68,68,0.1)",
  accent: "#6366F1",
  free: "#16A34A",
};

// ═══ DAY TABS ═══
export function generateDays(count: number = 5): DayOption[] {
  const NAMES = ["DIM", "LUN", "MAR", "MER", "JEU", "VEN", "SAM"];
  const days: DayOption[] = [];

  for (let i = 0; i < count; i++) {
    const dt = new Date();
    dt.setDate(dt.getDate() + i);
    const iso = dt.toISOString().split("T")[0];
    days.push({
      key: i,
      short: i === 0 ? "AUJ." : NAMES[dt.getDay()],
      date: dt.getDate(),
      iso,
    });
  }
  return days;
}

// ═══ FLAG CDN ═══
export function flagUrl(countryCode: string, size: number = 80): string {
  return `https://flagcdn.com/w${size}/${countryCode}.png`;
}

// ═══ ESPN CDN (club logos) ═══
// In production, build a lookup table from API-Sports or TheSportsDB
export function espnLogoUrl(sport: string, espnId: number, size: number = 500): string {
  const sportPath = sport === "basket" ? "nba" : "soccer";
  return `https://a.espncdn.com/i/teamlogos/${sportPath}/${size}/${espnId}.png`;
}

// ═══ API CONFIG ═══
export const API_BASE_URL = __DEV__
  ? "http://192.168.1.28:8000"     // Dev: local FastAPI
  : "https://api.sportzap.fr";  // Prod: deployed API
