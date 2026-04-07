/**
 * SportZap — Channel definitions
 *
 * Complete list of French TV channels relevant for sport,
 * grouped by bouquet/offer for the "Mes Chaînes" selector.
 *
 * Each channel has:
 *  - slug: matches backend channel.slug
 *  - name: display name
 *  - badge: visual config (label, bg, fg)
 *  - group: bouquet it belongs to
 *  - isFree: available on free TNT
 *  - description: what sports it carries (for onboarding)
 */

export interface ChannelDefinition {
  slug: string;
  name: string;
  badge: { label: string; bg: string; fg: string };
  group: ChannelGroup;
  isFree: boolean;
  sports: string; // short description of sport coverage
}

export type ChannelGroup =
  | "tnt"        // Free TNT channels
  | "canal"      // Canal+ bouquet
  | "bein"       // beIN Sports
  | "rmc"        // RMC Sport
  | "dazn"       // DAZN
  | "eurosport"  // Eurosport
  | "prime"      // Amazon Prime Video
  | "other";     // Others

export interface ChannelGroupInfo {
  id: ChannelGroup;
  label: string;
  description: string;
  icon: string;
  isFree: boolean;
}

// ── Group definitions ──
export const CHANNEL_GROUPS: ChannelGroupInfo[] = [
  {
    id: "tnt",
    label: "TNT Gratuite",
    description: "Chaînes accessibles à tous sans abonnement",
    icon: "📡",
    isFree: true,
  },
  {
    id: "canal",
    label: "Canal+",
    description: "Ligue 1, Top 14, F1, Premier League...",
    icon: "🎬",
    isFree: false,
  },
  {
    id: "dazn",
    label: "DAZN",
    description: "Ligue 1 (80% des matchs), boxe",
    icon: "⚡",
    isFree: false,
  },
  {
    id: "bein",
    label: "beIN Sports",
    description: "Liga, Serie A, NBA, Ligue des Champions...",
    icon: "🌍",
    isFree: false,
  },
  {
    id: "rmc",
    label: "RMC Sport",
    description: "Europa League, MMA, boxe",
    icon: "🏟️",
    isFree: false,
  },
  {
    id: "eurosport",
    label: "Eurosport",
    description: "Tennis, cyclisme, sports d'hiver, athlétisme",
    icon: "🌐",
    isFree: false,
  },
  {
    id: "prime",
    label: "Prime Video",
    description: "Ligue 1 (affiche du dimanche soir), Roland-Garros",
    icon: "📦",
    isFree: false,
  },
  {
    id: "other",
    label: "Autres",
    description: "Chaînes complémentaires",
    icon: "📺",
    isFree: false,
  },
];

// ── All channels ──
export const ALL_CHANNELS: ChannelDefinition[] = [
  // TNT
  { slug: "tf1", name: "TF1", badge: { label: "TF1", bg: "#0055A4", fg: "#fff" }, group: "tnt", isFree: true, sports: "Équipe de France, Coupe du monde" },
  { slug: "france-2", name: "France 2", badge: { label: "F·2", bg: "#E4003A", fg: "#fff" }, group: "tnt", isFree: true, sports: "Rugby, handball, JO, cyclisme" },
  { slug: "france-3", name: "France 3", badge: { label: "F·3", bg: "#0055A4", fg: "#fff" }, group: "tnt", isFree: true, sports: "Tour de France, sports régionaux" },
  { slug: "m6", name: "M6", badge: { label: "M6", bg: "#F59E0B", fg: "#000" }, group: "tnt", isFree: true, sports: "Europa League, basket" },
  { slug: "lequipe", name: "L'Équipe", badge: { label: "LÉQ", bg: "#FFD700", fg: "#000" }, group: "tnt", isFree: true, sports: "Multisport, débats, foot D2" },
  { slug: "sport-en-france", name: "Sport en France", badge: { label: "SEF", bg: "#0074E4", fg: "#fff" }, group: "tnt", isFree: true, sports: "Handball, hockey, volley, sports mineurs" },

  // Canal+
  { slug: "canal-plus", name: "Canal+", badge: { label: "C+", bg: "#1A1A1A", fg: "#fff" }, group: "canal", isFree: false, sports: "Top 14, F1, MotoGP, Premier League" },
  { slug: "canal-plus-sport", name: "Canal+ Sport", badge: { label: "C+S", bg: "#1A1A1A", fg: "#fff" }, group: "canal", isFree: false, sports: "Ligue 1, Champions League, rugby" },
  { slug: "canal-plus-foot", name: "Canal+ Foot", badge: { label: "C+F", bg: "#1A1A1A", fg: "#fff" }, group: "canal", isFree: false, sports: "Football en continu" },
  { slug: "infosport-plus", name: "Infosport+", badge: { label: "IS+", bg: "#1A1A1A", fg: "#fff" }, group: "canal", isFree: false, sports: "Résumés, actus sport" },

  // DAZN
  { slug: "dazn-1", name: "DAZN 1", badge: { label: "DAZN", bg: "#0C0C0E", fg: "#fff" }, group: "dazn", isFree: false, sports: "Ligue 1 (8 matchs/journée)" },
  { slug: "dazn-2", name: "DAZN 2", badge: { label: "DZ2", bg: "#0C0C0E", fg: "#fff" }, group: "dazn", isFree: false, sports: "Ligue 1, boxe" },

  // beIN Sports
  { slug: "bein-1", name: "beIN Sports 1", badge: { label: "beIN", bg: "#F7B500", fg: "#000" }, group: "bein", isFree: false, sports: "Liga, Serie A, Ligue des Champions" },
  { slug: "bein-2", name: "beIN Sports 2", badge: { label: "bN2", bg: "#F7B500", fg: "#000" }, group: "bein", isFree: false, sports: "NBA, football européen" },
  { slug: "bein-3", name: "beIN Sports 3", badge: { label: "bN3", bg: "#F7B500", fg: "#000" }, group: "bein", isFree: false, sports: "Football, multisport" },

  // RMC Sport
  { slug: "rmc-sport-1", name: "RMC Sport 1", badge: { label: "RMC", bg: "#D40000", fg: "#fff" }, group: "rmc", isFree: false, sports: "Europa League, MMA/UFC, boxe" },
  { slug: "rmc-sport-2", name: "RMC Sport 2", badge: { label: "RMC2", bg: "#D40000", fg: "#fff" }, group: "rmc", isFree: false, sports: "Football européen" },

  // Eurosport
  { slug: "eurosport-1", name: "Eurosport 1", badge: { label: "ES", bg: "#003DA6", fg: "#fff" }, group: "eurosport", isFree: false, sports: "Tennis (GC), cyclisme, ski, athlétisme" },
  { slug: "eurosport-2", name: "Eurosport 2", badge: { label: "ES2", bg: "#003DA6", fg: "#fff" }, group: "eurosport", isFree: false, sports: "Cyclisme, sports mécaniques" },

  // Prime Video
  { slug: "prime-video", name: "Prime Video", badge: { label: "𝐏𝐕", bg: "#00A8E1", fg: "#fff" }, group: "prime", isFree: false, sports: "Ligue 1 (dimanche 21h), Roland-Garros" },
];

// ── Helpers ──

export function getChannelsByGroup(group: ChannelGroup): ChannelDefinition[] {
  return ALL_CHANNELS.filter(ch => ch.group === group);
}

export function getChannelBySlug(slug: string): ChannelDefinition | undefined {
  return ALL_CHANNELS.find(ch => ch.slug === slug);
}

/** Default selection: all free TNT channels (everyone has them) */
export function getDefaultChannelSlugs(): Set<string> {
  return new Set(ALL_CHANNELS.filter(ch => ch.isFree).map(ch => ch.slug));
}

/** All slugs for quick "select all" */
export function getAllChannelSlugs(): Set<string> {
  return new Set(ALL_CHANNELS.map(ch => ch.slug));
}
