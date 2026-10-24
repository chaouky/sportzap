// ═══ API Response Types ═══
// Mirrors backend app/models.py

export type SportType =
  | "football" | "rugby" | "tennis" | "basket"
  | "f1" | "cyclisme" | "mma" | "handball"
  | "boxe" | "natation" | "athletisme" | "ski"
  | "golf" | "voile" | "motogp" | "volleyball"
  | "equitation" | "other";

export type EntityType = "club" | "country" | "player" | "event";

export type EventStatus = "upcoming" | "live" | "finished";

export interface Entity {
  name: string;
  type: EntityType;
  short?: string | null;
  country_code?: string | null;
  logo_url?: string | null;
  photo_url?: string | null;
}

export interface Channel {
  id: string;
  name: string;
  icon_url?: string | null;
  slug: string;
  is_free: boolean;
}

export interface SportEvent {
  id: string;
  sport: SportType;
  competition?: string | null;
  title: string;
  subtitle?: string | null;
  description?: string | null;
  team1?: Entity | null;
  team2?: Entity | null;
  channel: Channel;
  /** Toutes les chaînes du même match, une fois regroupées (voir mergeEvents). */
  channels?: Channel[];
  start: string; // ISO datetime — début de DIFFUSION sur la chaîne (avant-match inclus)
  end: string;   // ISO datetime
  /** Coup d'envoi officiel de la rencontre ; absent = on ne le connaît pas (voir start). */
  kickoff?: string | null;
  kickoff_source?: "espn" | "estimate" | null;
  status: EventStatus;
  score1?: number | null;
  score2?: number | null;
  minute?: string | null;
  result?: string | null;
}

export interface DaySchedule {
  date: string; // YYYY-MM-DD
  event_count: number;
  live_count: number;
  events: SportEvent[];
}

// ═══ App-level types ═══

export interface SportFilter {
  id: SportType | "all";
  label: string;
  color: string;
}

export interface DayOption {
  key: number;
  short: string;
  date: number;
  iso: string; // YYYY-MM-DD
}

export type TimeBlock = "EN DIRECT" | "MATIN" | "APRÈS-MIDI" | "SOIRÉE";
