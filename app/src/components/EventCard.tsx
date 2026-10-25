/**
 * EventCard — direction « Night Match ».
 *
 * Même carte pleine largeur pour tous les matchs ; seul le statut change :
 *   - live    : bordure lime + pastille « DEPUIS hh:mm »
 *   - à venir : bordure discrète + heure du coup d'envoi en grand
 * Les chaînes s'affichent avec leur logo officiel (repli : pastille texte).
 *
 * Chaque carte annonce son sport (pictogramme + libellé) et sa compétition.
 * Un match = une carte : toutes les chaînes (`event.channels`) y figurent.
 */
import React, { useState } from "react";
import { View, Text, Image, TouchableOpacity, StyleSheet } from "react-native";
import { Channel, Entity, SportEvent } from "../types";
import { COLORS, FONTS, getChannelBadge, kickoffOf, parisTime } from "../constants";
import { describeEvent } from "../services/describeEvent";
import { getChannelLogo } from "../constants/channelLogos";
import { EntityAvatar } from "./EntityAvatar";
import { Icon } from "./Icon";
import { SportGlyph } from "./SportGlyph";

interface Props {
  event: SportEvent;
  onPress?: () => void;
  onBellPress?: () => void;
  isBellActive?: boolean;
  isFavorite?: boolean;
}

// Retire les préfixes/suffixes administratifs : « Olympique de Marseille » → « Marseille »
const CLUB_PREFIX =
  /^(?:olympique de |olympique |stade de |stade |racing club de |racing club |football club |1\. fc |fc |as |ac |aj |rcd |rc |sc |ssc |sl |sv |tsg |vfb |vfl |ud |cd |ca |us )/i;
const CLUB_SUFFIX = / (?:football club|fc|cf|ac|sco|hsc|fco)$/i;
const CLUB_SPECIAL: Record<string, string> = { lyonnais: "Lyon", rennais: "Rennes", brestois: "Brest" };

/** Libellé court et lisible d'un club, à taille de police constante. */
function teamLabel(e?: Entity | null): string {
  if (!e) return "?";
  if (e.short && e.short.length >= 3) return e.short;
  const base = e.name.trim();
  let n = base.replace(CLUB_PREFIX, "").replace(CLUB_SUFFIX, "").trim();
  n = CLUB_SPECIAL[n.toLowerCase()] ?? n;
  return n.length >= 3 ? n : base;
}

/** Les URL du flux Canal+ contiennent des gabarits à remplir. */
function logoUrl(raw?: string | null): string | null {
  if (!raw) return null;
  return raw
    .replace("{resolutionXY}", "320x240")
    .replace("{imageQualityPercentage}", "100");
}

const LOGO_H = 22;   // hauteur de la pastille ; le logo y occupe toujours la même hauteur (14 px)
const LOGO_PAD_X = 5;
const LOGO_PAD_Y = 4;

/** Largeur d'une vignette-logo (même calcul pour l'affichage et pour le nombre de vignettes qui tiennent). */
function widthForRatio(ratio: number): number {
  const inner = LOGO_H - 2 * LOGO_PAD_Y;   // hauteur du logo : identique pour toutes les chaînes
  return Math.min(130, Math.max(30, Math.round(inner * ratio) + 2 * LOGO_PAD_X));
}

function tileWidth(channel: Channel): number {
  const local = getChannelLogo(channel.name);
  if (local) return widthForRatio(local.ratio);
  return logoUrl(channel.icon_url) ? widthForRatio(2.2) : 52;
}

const TILES_MAX_WIDTH = 250; // carte 393 px − marges − cloche

export function ChannelTile({ channel }: { channel: Channel }) {
  const [failed, setFailed] = useState(false);
  const local = getChannelLogo(channel.name);
  const remote = logoUrl(channel.icon_url);

  if (local || (remote && !failed)) {
    // Largeur proportionnelle au logo recadré, bornée pour ne pas écraser le reste
    const ratio = local ? local.ratio : 2.2;
    const width = widthForRatio(ratio);
    return (
      <View
        style={[
          styles.logoTile,
          { width, height: LOGO_H },
          local?.onDark && styles.logoTileDark,
        ]}
      >
        <Image
          source={local ? local.src : { uri: remote as string }}
          style={styles.logoImg}
          resizeMode="contain"
          onError={() => setFailed(true)}
          accessibilityLabel={channel.name}
        />
      </View>
    );
  }
  const badge = getChannelBadge(channel.slug);
  const label = badge.label === "TV" ? channel.name.slice(0, 4).toUpperCase() : badge.label;
  return (
    <View style={[styles.tile, { backgroundColor: badge.bg }]}>
      <Text style={[styles.tileText, { color: badge.fg }]} numberOfLines={1} allowFontScaling={false}>
        {label}
      </Text>
    </View>
  );
}

export function EventCard({ event, onPress, onBellPress, isBellActive, isFavorite }: Props) {
  const channels = event.channels && event.channels.length > 0 ? event.channels : [event.channel];
  // Une seule vignette par logo (Canal+ Live 1…19 partagent le même)
  // « Diffuseur à confirmer » : match du calendrier officiel absent du flux TV
  const known = channels.filter(c => c.slug !== "a-confirmer");
  const shownChannels = known.filter(
    (c, i) => known.findIndex(o => (o.icon_url || o.name) === (c.icon_url || c.name)) === i,
  );
  // Autant de logos que la largeur le permet (au moins un), le reste en « +N »
  const visibleChannels: Channel[] = [];
  let used = 0;
  for (const c of shownChannels) {
    const w = tileWidth(c) + 6;
    if (visibleChannels.length > 0 && used + w > TILES_MAX_WIDTH) break;
    visibleChannels.push(c);
    used += w;
  }
  const isLive = event.status === "live";
  const hasTeams = !!(event.team1 && event.team2);
  const hasScore = event.score1 != null && event.score2 != null;
  const time = parisTime(kickoffOf(event));
  const info = describeEvent(event);

  const teamsTitle = hasTeams ? `${teamLabel(event.team1)} – ${teamLabel(event.team2)}` : info.headline;

  // « ⚽ FOOTBALL · PREMIER LEAGUE » (+ étoile si favori)
  const sportLine = (
    <View style={styles.sportRow}>
      <SportGlyph name={info.glyph} size={18} color={COLORS.textSecondary} />
      <Text style={styles.sportText} numberOfLines={1}>
        <Text style={styles.sportName}>{info.sportLabel}</Text>
        {info.context ? ` · ${info.context}` : ""}
      </Text>
      {isFavorite && <Icon name="star" size={14} color={COLORS.favorite} filled />}
    </View>
  );

  const footer = (
    <View style={styles.footer}>
      {shownChannels.length > 0 && (
      <View style={styles.tiles}>
        {visibleChannels.map(c => (
          <ChannelTile key={c.name} channel={c} />
        ))}
        {shownChannels.length > visibleChannels.length && (
          <Text style={styles.more}>+{shownChannels.length - visibleChannels.length}</Text>
        )}
      </View>
      )}
      {shownChannels.length === 0 ? (
        <Text style={[styles.channelNames, styles.channelPending]} numberOfLines={1}>
          Diffuseur à confirmer
        </Text>
      ) : (
        <View style={styles.spacer} />
      )}
      <TouchableOpacity
        onPress={onBellPress}
        hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        accessibilityLabel={isBellActive ? "Retirer le rappel" : "Me rappeler ce match"}
        style={styles.bell}
      >
        <Icon
          name="bell"
          size={18}
          color={isBellActive ? COLORS.accent : COLORS.textSecondary}
          filled={!!isBellActive}
        />
      </TouchableOpacity>
    </View>
  );

  return (
    <TouchableOpacity
      style={[styles.card, isLive && styles.cardLive]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.topRow}>
        {sportLine}
        {isLive ? (
          <View style={styles.liveBadge}>
            <Text style={styles.liveBadgeText} allowFontScaling={false}>DEPUIS {time}</Text>
          </View>
        ) : (
          <Text style={styles.timeText} allowFontScaling={false}>{time}</Text>
        )}
      </View>

      {hasTeams ? (
        <View style={styles.vsRow}>
          <View style={styles.side}>
            <EntityAvatar entity={event.team1} size={36} />
            <Text style={styles.sideName} numberOfLines={2} allowFontScaling={false}>
              {teamLabel(event.team1)}
            </Text>
          </View>
          <View style={styles.center}>
            <Text style={hasScore ? styles.score : styles.vs} allowFontScaling={false}>
              {hasScore ? `${event.score1} – ${event.score2}` : "VS"}
            </Text>
          </View>
          <View style={styles.side}>
            <EntityAvatar entity={event.team2} size={36} />
            <Text style={styles.sideName} numberOfLines={2} allowFontScaling={false}>
              {teamLabel(event.team2)}
            </Text>
          </View>
        </View>
      ) : (
        <Text style={styles.soloTitle} numberOfLines={3}>{teamsTitle}</Text>
      )}

      {footer}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 14,
    paddingVertical: 11,
    gap: 8,
    marginBottom: 8,
  },
  cardLive: { borderColor: COLORS.accent },
  timeText: {
    fontFamily: FONTS.display,
    fontSize: 24,
    lineHeight: 26,
    color: COLORS.text,
  },

  topRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 10 },
  sportRow: { flexDirection: "row", alignItems: "center", gap: 7, flexShrink: 1, minWidth: 0 },
  sportText: {
    flexShrink: 1,
    fontFamily: FONTS.bodyMedium,
    fontSize: 12,
    letterSpacing: 0.6,
    textTransform: "uppercase",
    color: COLORS.textSecondary,
  },
  sportName: { fontFamily: FONTS.bodySemi, color: COLORS.text },
  liveBadge: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: 9,
    paddingVertical: 2,
    borderRadius: 6,
  },
  liveBadgeText: {
    fontFamily: FONTS.displayBold,
    fontSize: 14,
    letterSpacing: 1,
    color: COLORS.onAccent,
  },

  vsRow: { flexDirection: "row", alignItems: "flex-start" },
  side: { flex: 1, alignItems: "center", gap: 4, minWidth: 0 },
  center: { width: 56, height: 36, alignItems: "center", justifyContent: "center" },
  sideName: {
    alignSelf: "stretch",
    fontFamily: FONTS.displayBold,
    fontSize: 20,
    lineHeight: 22,
    textAlign: "center",
    textTransform: "uppercase",
    color: COLORS.text,
  },
  vs: {
    fontFamily: FONTS.displaySemi,
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  score: {
    fontFamily: FONTS.display,
    fontSize: 26,
    color: COLORS.accent,
  },
  soloTitle: {
    fontFamily: FONTS.displayBold,
    fontSize: 22,
    lineHeight: 24,
    textTransform: "uppercase",
    color: COLORS.text,
  },
  title: {
    fontFamily: FONTS.displayBold,
    fontSize: 25,
    lineHeight: 27,
    textTransform: "uppercase",
    color: COLORS.text,
  },

  footer: { flexDirection: "row", alignItems: "center", gap: 8 },
  tiles: { flexDirection: "row", alignItems: "center", gap: 6 },
  tile: {
    minWidth: 40,
    height: LOGO_H,
    paddingHorizontal: 7,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: COLORS.borderActive,
    alignItems: "center",
    justifyContent: "center",
  },
  logoTile: {
    borderRadius: 8,
    backgroundColor: "#E6EAF4",
    paddingHorizontal: LOGO_PAD_X,
    paddingVertical: LOGO_PAD_Y,
    alignItems: "center",
    justifyContent: "center",
  },
  logoTileDark: {
    backgroundColor: "#0A0E1A",
    borderWidth: 1,
    borderColor: COLORS.borderActive,
  },
  logoImg: { width: "100%", height: "100%" },
  tileText: { fontFamily: FONTS.displayBold, fontSize: 13, letterSpacing: 0.2 },
  more: { fontFamily: FONTS.bodySemi, fontSize: 12, color: COLORS.textSecondary },
  channelNames: {
    flex: 1,
    fontFamily: FONTS.body,
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  spacer: { flex: 1 },
  channelPending: { fontFamily: FONTS.bodyMedium, fontStyle: "italic", color: COLORS.textTertiary },
  bell: { padding: 4 },
});
