/**
 * describeEvent — transforme un événement brut (titre / sous-titre / compétition
 * souvent redondants ou génériques) en trois informations lisibles :
 *   - le sport (libellé + pictogramme)
 *   - le contexte (compétition, épreuve)
 *   - le titre principal (équipes, ou phase / étape / session)
 */
import { SportEvent, SportType } from "../types";
import type { GlyphName } from "../components/SportGlyph";

const SPORT_LABEL: Record<string, string> = {
  football: "Football", rugby: "Rugby", tennis: "Tennis", basket: "Basket",
  f1: "Formule 1", cyclisme: "Cyclisme", mma: "Combat", handball: "Handball",
  boxe: "Boxe", natation: "Natation", athletisme: "Athlétisme", ski: "Ski",
  golf: "Golf", voile: "Voile", motogp: "Moto", volleyball: "Volley",
  equitation: "Équitation", foot_us: "Football américain", other: "Sport",
};

const SPORT_GLYPH: Record<string, GlyphName> = {
  football: "football", rugby: "rugby", tennis: "tennis", basket: "basket",
  f1: "flag", cyclisme: "cycling", mma: "fight", handball: "ball", boxe: "fight",
  natation: "swim", athletisme: "stopwatch", ski: "mountain", golf: "golf",
  voile: "sail", motogp: "flag", volleyball: "ball", equitation: "horseshoe",
  foot_us: "rugby", other: "trophy",
};

// Le libellé (ex. « Judo », « Snooker ») prime sur la catégorie large du backend.
// [motif, pictogramme, libellé utilisé quand le sport n'est pas annoncé en préfixe]
const LABEL_RULES: [RegExp, GlyphName, string][] = [
  [/football am[eé]ricain|\bnfl\b/i, "rugby", "Football américain"],
  [/moto ?gp|moto ?[23]\b|superbike|motocross|rall?y|formule|\bf[123]\b|indycar|nascar|endurance|\bwec\b|dtm|karting/i, "flag", "Sport auto-moto"],
  [/football|soccer/i, "football", "Football"],
  [/rugby/i, "rugby", "Rugby"],
  [/basket|\bnba\b/i, "basket", "Basket"],
  [/tennis|padel|squash|badminton|ping/i, "tennis", "Tennis"],
  [/cyclo|cyclisme|v[eé]lo|\bvtt\b|mountain bike|enduro|\bbmx\b|tour de/i, "cycling", "Cyclisme"],
  [/short-?track|patinage|curling|hockey/i, "puck", "Sports de glace"],
  [/ski|snowboard|biathlon|escalade|climbing|alpinisme|luge|bobsleigh|skeleton/i, "mountain", "Montagne"],
  [/golf/i, "golf", "Golf"],
  [/judo|mma|ufc|boxe|lutte|karat|taekwondo|jiu|kick|escrime|sumo/i, "fight", "Combat"],
  [/nata|plong|water-?polo|aviron|cano[eë]|kayak|surf/i, "swim", "Sports nautiques"],
  [/athl[eé]|marathon|course [àa] pied|trail|cross-country/i, "stopwatch", "Athlétisme"],
  [/voile|sail|nautique/i, "sail", "Voile"],
  [/[eé]quitation|hippisme|trot|galop|saut d'obstacles/i, "horseshoe", "Équitation"],
  [/snooker|billard|\bpool\b/i, "billiard", "Snooker"],
  [/handball|volley|baseball|softball|beach/i, "ball", "Sport collectif"],
];

const norm = (s?: string | null) =>
  (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");

// Sous-titres venus d'un flux étranger (« Gran Premio Francia », « Round 3 »…) : on les ignore
const FOREIGN_SUB = /\b(gran premio|gran premi|gro(?:ss|ß)er preis|gp of|grand prix of|qualifying|practice|round \d|finals?\b|heat \d|session \d|race \d)\b/i;

const PHASE = /(finale|quart|demi|manche|qualif|tour\b|course|essai|journ[eé]e|[eé]tape|phase|groupe|poule|session|relais|sprint|mass start|slalom|descente|super-?g|g[eé]ant)/i;

function sportOf(e: SportEvent): { label: string; glyph: GlyphName; prefix: string | null } {
  const m = /^([^:|]{2,26}?)\s*:\s+/.exec(e.title);
  const prefix = m ? m[1].trim() : null;
  const byPrefix = prefix ? LABEL_RULES.find(([re]) => re.test(prefix)) : undefined;

  // Préfixe reconnu (« Judo : … », « Moto GP : … ») ou catégorie trop large (other/mma)
  if (prefix && (byPrefix || e.sport === "other" || e.sport === "mma")) {
    return { label: prefix, glyph: byPrefix?.[1] ?? SPORT_GLYPH[e.sport] ?? "trophy", prefix };
  }
  // Catégorie « autre » sans préfixe : on devine d'après le texte (VTT, short-track…)
  if (e.sport === "other") {
    const text = `${e.title} ${e.competition ?? ""} ${e.subtitle ?? ""}`;
    const hit = LABEL_RULES.find(([re]) => re.test(text));
    if (hit) return { label: hit[2], glyph: hit[1], prefix };
  }
  const key: SportType = e.sport;
  return { label: SPORT_LABEL[key] ?? "Sport", glyph: SPORT_GLYPH[key] ?? "trophy", prefix };
}

/**
 * « Epreuve de Sölden. Slalom géant dames. 1re manche. Coupe du monde » →
 * « Slalom géant dames · 1re manche » (sans répéter la compétition, 2 pièces max).
 */
function cleanSub(sub: string, ctx: string | null): string {
  const s = sub.trim().replace(/^[ée]preuve de [^.]+\.\s*/i, "");
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of s.split(/\s*\|\s*|\.\s+|\s+:\s+/)) {
    const part = raw.replace(/\.$/, "").trim();
    const k = norm(part);
    if (!part || seen.has(k)) continue;
    if (ctx && (norm(ctx).includes(k) || k.includes(norm(ctx)))) continue;
    if (/^coupe du monde|^championnat du monde/i.test(part) && out.length) continue;
    seen.add(k);
    out.push(part);
  }
  return out.slice(0, 2).join(" · ");
}

export interface EventInfo {
  glyph: GlyphName;
  sportLabel: string;
  /** Compétition / épreuve, null si elle est déjà le titre principal. */
  context: string | null;
  /** Titre principal pour les événements sans équipes. */
  headline: string;
}

export function describeEvent(e: SportEvent): EventInfo {
  const { label, glyph, prefix } = sportOf(e);
  const hasTeams = !!(e.team1 && e.team2);

  // Compétition : retire « Football. » / « Basket-ball. » en tête
  const cleanComp = (c?: string | null) =>
    (c || "").replace(/^(football|basket-?ball|rugby|handball|volley-?ball)\.\s*/i, "").trim() || null;

  let comp = cleanComp(e.competition);
  // « Compétition | Affiche » : quand le 1er morceau répète la compétition ou le sport,
  // c'est le morceau après la barre qui nomme vraiment l'épreuve.
  const pieces = (prefix ? e.title.replace(/^[^:]+:\s+/, "") : e.title).split(" | ").map(p => p.trim()).filter(Boolean);
  const titleRest = (pieces.length > 1 && (norm(pieces[0]) === norm(comp) || norm(pieces[0]) === norm(label))
    ? pieces[1] : pieces[0]) || null;

  if (hasTeams) {
    return { glyph, sportLabel: label, context: comp, headline: "" };
  }

  // Cas où la « compétition » est en fait la phase (ex. « Demi-finale »)
  let ctx: string | null = comp;
  let sub: string | null = e.subtitle ? e.subtitle.trim() : null;
  if (sub && FOREIGN_SUB.test(sub)) sub = null;
  if (comp && PHASE.test(comp) && titleRest && norm(titleRest) !== norm(comp)) {
    sub = sub && norm(sub) !== norm(titleRest) ? sub : comp;
    ctx = titleRest;
  } else if (!ctx && titleRest) {
    ctx = titleRest;
  }
  if (ctx && norm(ctx) === norm(label)) ctx = null;

  let cleaned: string | null = sub ? cleanSub(sub, ctx) : null;
  const sameAsLabel = (v: string) => norm(v) === norm(label) || norm(label).includes(norm(v));
  if (cleaned && (sameAsLabel(cleaned) || (ctx && norm(cleaned) === norm(ctx)))) cleaned = null;
  if (cleaned && /^[ée]mission du/i.test(cleaned)) cleaned = null;

  const headline = cleaned || ctx || titleRest || e.title;
  const context = ctx && norm(ctx) !== norm(headline) ? ctx : null;
  return { glyph, sportLabel: label, context, headline };
}
