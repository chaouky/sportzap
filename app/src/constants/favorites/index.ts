/**
 * SportZap — Favorites definitions
 *
 * Defines what users can follow:
 *  - Teams (clubs + national teams)
 *  - Competitions (Ligue 1, Champions League, Top 14...)
 *  - Sports (football, tennis...)
 *
 * Each followable has a visual identity that matches
 * the entity registry on the backend.
 */

export type FavoriteType = "team" | "competition" | "sport";

export interface Followable {
  id: string;          // Unique key: "team:psg", "comp:ligue-1"
  type: FavoriteType;
  name: string;        // Display: "Paris Saint-Germain"
  short: string;       // Short: "PSG"
  sport: string;
  badgeBg: string;     // Badge or accent color
  badgeFg: string;
  logoUrl?: string;
  flagCode?: string;   // For national teams
  aliases: string[];   // Match against XMLTV event data
}

// ═══ COMPETITIONS ═══
export const COMPETITIONS: Followable[] = [
  // Football France
  { id: "comp:ligue-1", type: "competition", name: "Ligue 1", short: "L1", sport: "football",
    badgeBg: "#1B3C73", badgeFg: "#fff", aliases: ["Ligue 1", "Ligue 1 Uber Eats", "Ligue 1 McDonald's"] },
  { id: "comp:ligue-2", type: "competition", name: "Ligue 2", short: "L2", sport: "football",
    badgeBg: "#4A7FC1", badgeFg: "#fff", aliases: ["Ligue 2", "Ligue 2 BKT"] },
  { id: "comp:coupe-france", type: "competition", name: "Coupe de France", short: "CdF", sport: "football",
    badgeBg: "#002395", badgeFg: "#fff", aliases: ["Coupe de France"] },

  // Football Europe
  { id: "comp:champions-league", type: "competition", name: "Ligue des Champions", short: "LdC", sport: "football",
    badgeBg: "#0D1541", badgeFg: "#fff", aliases: ["Ligue des Champions", "Champions League", "UEFA Champions League"] },
  { id: "comp:europa-league", type: "competition", name: "Europa League", short: "EL", sport: "football",
    badgeBg: "#F68E1E", badgeFg: "#000", aliases: ["Europa League", "Ligue Europa", "UEFA Europa League"] },
  { id: "comp:premier-league", type: "competition", name: "Premier League", short: "PL", sport: "football",
    badgeBg: "#3D195B", badgeFg: "#fff", aliases: ["Premier League"] },
  { id: "comp:liga", type: "competition", name: "Liga", short: "Liga", sport: "football",
    badgeBg: "#EE2523", badgeFg: "#fff", aliases: ["Liga", "La Liga", "LaLiga"] },
  { id: "comp:serie-a", type: "competition", name: "Serie A", short: "SerA", sport: "football",
    badgeBg: "#024494", badgeFg: "#fff", aliases: ["Serie A"] },
  { id: "comp:bundesliga", type: "competition", name: "Bundesliga", short: "BuLi", sport: "football",
    badgeBg: "#D20515", badgeFg: "#fff", aliases: ["Bundesliga"] },

  // Football international
  { id: "comp:coupe-du-monde", type: "competition", name: "Coupe du Monde", short: "CdM", sport: "football",
    badgeBg: "#56042C", badgeFg: "#fff", aliases: ["Coupe du Monde", "Coupe du monde", "FIFA World Cup", "Mondial"] },
  { id: "comp:euro", type: "competition", name: "Euro", short: "Euro", sport: "football",
    badgeBg: "#003DA5", badgeFg: "#fff", aliases: ["Euro ", "Championnat d'Europe", "UEFA Euro"] },
  { id: "comp:amical", type: "competition", name: "Match Amical", short: "Amical", sport: "football",
    badgeBg: "#6B7280", badgeFg: "#fff", aliases: ["Match Amical", "Amical", "Match amical international"] },

  // Rugby
  { id: "comp:top-14", type: "competition", name: "Top 14", short: "T14", sport: "rugby",
    badgeBg: "#1B2A4A", badgeFg: "#fff", aliases: ["Top 14"] },
  { id: "comp:champions-cup", type: "competition", name: "Champions Cup", short: "CCup", sport: "rugby",
    badgeBg: "#00205B", badgeFg: "#fff", aliases: ["Champions Cup", "Coupe d'Europe"] },
  { id: "comp:six-nations", type: "competition", name: "Six Nations", short: "6N", sport: "rugby",
    badgeBg: "#00843D", badgeFg: "#fff", aliases: ["Six Nations", "Tournoi des Six Nations", "6 Nations"] },

  // Tennis
  { id: "comp:roland-garros", type: "competition", name: "Roland-Garros", short: "RG", sport: "tennis",
    badgeBg: "#D04A35", badgeFg: "#fff", aliases: ["Roland-Garros", "Roland Garros"] },
  { id: "comp:wimbledon", type: "competition", name: "Wimbledon", short: "Wim", sport: "tennis",
    badgeBg: "#00703C", badgeFg: "#fff", aliases: ["Wimbledon"] },
  { id: "comp:masters-1000", type: "competition", name: "Masters 1000", short: "M1000", sport: "tennis",
    badgeBg: "#2563EB", badgeFg: "#fff", aliases: ["Masters 1000", "ATP Masters"] },

  // Basketball
  { id: "comp:nba", type: "competition", name: "NBA", short: "NBA", sport: "basket",
    badgeBg: "#1D428A", badgeFg: "#fff", aliases: ["NBA"] },
  { id: "comp:betclic-elite", type: "competition", name: "Betclic Élite", short: "BÉ", sport: "basket",
    badgeBg: "#002B5C", badgeFg: "#fff", aliases: ["Betclic Élite", "Betclic Elite", "Pro A"] },

  // F1
  { id: "comp:f1", type: "competition", name: "Formule 1", short: "F1", sport: "f1",
    badgeBg: "#E10600", badgeFg: "#fff", aliases: ["Formule 1", "F1", "Grand Prix"] },

  // MMA
  { id: "comp:ufc", type: "competition", name: "UFC", short: "UFC", sport: "mma",
    badgeBg: "#D20A0A", badgeFg: "#fff", aliases: ["UFC"] },
  { id: "comp:pfl", type: "competition", name: "PFL", short: "PFL", sport: "mma",
    badgeBg: "#1A1A2E", badgeFg: "#fff", aliases: ["PFL"] },

  // Cyclisme
  { id: "comp:tour-de-france", type: "competition", name: "Tour de France", short: "TdF", sport: "cyclisme",
    badgeBg: "#FFD700", badgeFg: "#000", aliases: ["Tour de France"] },

  // Handball
  { id: "comp:golden-league", type: "competition", name: "Golden League", short: "GL", sport: "handball",
    badgeBg: "#F7B500", badgeFg: "#000", aliases: ["Golden League"] },
];

// ═══ POPULAR TEAMS (for quick-follow onboarding) ═══
export const POPULAR_TEAMS: Followable[] = [
  // Ligue 1
  { id: "team:psg", type: "team", name: "Paris Saint-Germain", short: "PSG", sport: "football",
    badgeBg: "#004170", badgeFg: "#fff", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    aliases: ["Paris-SG", "PSG", "Paris Saint-Germain", "Paris SG"] },
  { id: "team:om", type: "team", name: "Olympique de Marseille", short: "OM", sport: "football",
    badgeBg: "#2FAEE0", badgeFg: "#fff", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/176.png",
    aliases: ["OM", "Olympique de Marseille", "Marseille"] },
  { id: "team:ol", type: "team", name: "Olympique Lyonnais", short: "OL", sport: "football",
    badgeBg: "#1D4A8D", badgeFg: "#fff", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/167.png",
    aliases: ["OL", "Olympique Lyonnais", "Lyon"] },
  { id: "team:monaco", type: "team", name: "AS Monaco", short: "Monaco", sport: "football",
    badgeBg: "#E4002B", badgeFg: "#fff", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/174.png",
    aliases: ["Monaco", "AS Monaco"] },
  { id: "team:losc", type: "team", name: "LOSC Lille", short: "LOSC", sport: "football",
    badgeBg: "#E4002B", badgeFg: "#fff", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/166.png",
    aliases: ["LOSC", "Lille", "LOSC Lille"] },
  { id: "team:lens", type: "team", name: "RC Lens", short: "Lens", sport: "football",
    badgeBg: "#F1C40F", badgeFg: "#E4002B", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/171.png",
    aliases: ["RC Lens", "Lens"] },

  // National teams
  { id: "team:france-foot", type: "team", name: "Équipe de France", short: "France", sport: "football",
    badgeBg: "#002395", badgeFg: "#fff", flagCode: "fr",
    aliases: ["France", "Équipe de France", "Bleus"] },
  { id: "team:france-rugby", type: "team", name: "XV de France", short: "XV de Fr.", sport: "rugby",
    badgeBg: "#002395", badgeFg: "#fff", flagCode: "fr",
    aliases: ["France"] },
  { id: "team:france-hand", type: "team", name: "France Handball", short: "Fr. Hand", sport: "handball",
    badgeBg: "#002395", badgeFg: "#fff", flagCode: "fr",
    aliases: ["France"] },

  // Top 14
  { id: "team:stade-toulousain", type: "team", name: "Stade Toulousain", short: "Toulouse", sport: "rugby",
    badgeBg: "#E4002B", badgeFg: "#fff",
    aliases: ["Stade Toulousain", "Toulouse", "ST"] },
  { id: "team:racing-92", type: "team", name: "Racing 92", short: "Racing", sport: "rugby",
    badgeBg: "#5BC5F2", badgeFg: "#1B2A4A",
    aliases: ["Racing 92", "Racing"] },
  { id: "team:la-rochelle", type: "team", name: "Stade Rochelais", short: "La Rochelle", sport: "rugby",
    badgeBg: "#F1C40F", badgeFg: "#000",
    aliases: ["La Rochelle", "Stade Rochelais"] },

  // European clubs
  { id: "team:real-madrid", type: "team", name: "Real Madrid", short: "Real", sport: "football",
    badgeBg: "#FEBE10", badgeFg: "#00529F", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    aliases: ["Real Madrid", "R. Madrid"] },
  { id: "team:barca", type: "team", name: "FC Barcelone", short: "Barça", sport: "football",
    badgeBg: "#A50044", badgeFg: "#fff", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    aliases: ["FC Barcelone", "Barcelone", "Barça", "Barcelona"] },
  { id: "team:arsenal", type: "team", name: "Arsenal FC", short: "Arsenal", sport: "football",
    badgeBg: "#EF0107", badgeFg: "#fff", logoUrl: "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    aliases: ["Arsenal FC", "Arsenal"] },
  { id: "team:lakers", type: "team", name: "Los Angeles Lakers", short: "Lakers", sport: "basket",
    badgeBg: "#552583", badgeFg: "#FDB927", logoUrl: "https://a.espncdn.com/i/teamlogos/nba/500/13.png",
    aliases: ["Lakers", "Los Angeles Lakers", "LA Lakers"] },
];

// ═══ Helper: match an event against favorites ═══

/**
 * Check if a sport event matches any of the user's favorites.
 * Returns the matching favorite IDs.
 */
export function matchEventToFavorites(
  event: { team1?: { name: string } | null; team2?: { name: string } | null; competition?: string | null; sport: string },
  favoriteIds: Set<string>,
): string[] {
  const matches: string[] = [];
  const allFollowables = [...COMPETITIONS, ...POPULAR_TEAMS];

  for (const fav of allFollowables) {
    if (!favoriteIds.has(fav.id)) continue;

    // Check competition match
    if (fav.type === "competition" && event.competition) {
      if (fav.aliases.some(a => event.competition!.toLowerCase().includes(a.toLowerCase()))) {
        matches.push(fav.id);
        continue;
      }
    }

    // Check team match
    if (fav.type === "team") {
      const t1 = event.team1?.name?.toLowerCase() || "";
      const t2 = event.team2?.name?.toLowerCase() || "";
      if (fav.aliases.some(a => {
        const al = a.toLowerCase();
        return t1.includes(al) || t2.includes(al);
      })) {
        matches.push(fav.id);
      }
    }
  }

  return matches;
}
