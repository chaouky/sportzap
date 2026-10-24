/**
 * EventCard — direction « Night Match ».
 *
 * Deux variantes selon le statut :
 *   - live    : carte pleine largeur, bordure lime, équipes + chaînes
 *   - à venir : rail d'heure à gauche (grande heure condensée) + carte
 *
 * Un match = une carte : toutes les chaînes (`event.channels`) y figurent.
 */
import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { Channel, Entity, SportEvent } from "../types";
import { COLORS, FONTS, getChannelBadge, kickoffOf, parisTime } from "../constants";
import { EntityAvatar } from "./EntityAvatar";
import { Icon } from "./Icon";

interface Props {
  event: SportEvent;
  onPress?: () => void;
  onBellPress?: () => void;
  isBellActive?: boolean;
  isFavorite?: boolean;
}

function teamLabel(e?: Entity | null): string {
  if (!e) return "?";
  return e.short && e.short.length >= 3 ? e.short : e.name;
}

function ChannelTile({ channel }: { channel: Channel }) {
  const badge = getChannelBadge(channel.slug);
  const label = badge.label === "TV" ? channel.name.slice(0, 4).toUpperCase() : badge.label;
  return (
    <View style={[styles.tile, { backgroundColor: badge.bg }]}>
      <Text style={[styles.tileText, { color: badge.fg }]} numberOfLines={1}>
        {label}
      </Text>
    </View>
  );
}

export function EventCard({ event, onPress, onBellPress, isBellActive, isFavorite }: Props) {
  const channels = event.channels && event.channels.length > 0 ? event.channels : [event.channel];
  const channelNames = Array.from(new Set(channels.map(c => c.name))).join(" · ");
  const isLive = event.status === "live";
  const hasTeams = !!(event.team1 && event.team2);
  const hasScore = event.score1 != null && event.score2 != null;
  const time = parisTime(kickoffOf(event));

  const comp =
    event.competition && !event.title.toLowerCase().includes(event.competition.toLowerCase())
      ? event.competition
      : null;
  const mainTitle = hasTeams
    ? `${teamLabel(event.team1)} – ${teamLabel(event.team2)}`
    : event.subtitle || event.title;

  const footer = (
    <View style={styles.footer}>
      <View style={styles.tiles}>
        {channels.slice(0, 3).map(c => (
          <ChannelTile key={c.name} channel={c} />
        ))}
        {channels.length > 3 && <Text style={styles.more}>+{channels.length - 3}</Text>}
      </View>
      <Text style={styles.channelNames} numberOfLines={1}>{channelNames}</Text>
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

  // ───────────── LIVE ─────────────
  if (isLive) {
    return (
      <TouchableOpacity style={[styles.card, styles.cardLive]} onPress={onPress} activeOpacity={0.8}>
        <View style={styles.topRow}>
          <View style={styles.compWrap}>
            {isFavorite && <Icon name="star" size={14} color={COLORS.favorite} filled />}
            <Text style={styles.comp} numberOfLines={1}>{comp ?? ""}</Text>
          </View>
          <View style={styles.liveBadge}>
            <Text style={styles.liveBadgeText}>DEPUIS {time}</Text>
          </View>
        </View>

        {hasTeams ? (
          <View style={styles.vsRow}>
            <View style={styles.side}>
              <EntityAvatar entity={event.team1} size={40} />
              <Text style={styles.sideName} numberOfLines={2}>{teamLabel(event.team1)}</Text>
            </View>
            <Text style={hasScore ? styles.score : styles.vs}>
              {hasScore ? `${event.score1} – ${event.score2}` : "VS"}
            </Text>
            <View style={[styles.side, styles.sideRight]}>
              <Text style={[styles.sideName, { textAlign: "right" }]} numberOfLines={2}>
                {teamLabel(event.team2)}
              </Text>
              <EntityAvatar entity={event.team2} size={40} />
            </View>
          </View>
        ) : (
          <Text style={styles.soloTitle} numberOfLines={2}>{mainTitle}</Text>
        )}

        {footer}
      </TouchableOpacity>
    );
  }

  // ───────────── À VENIR ─────────────
  return (
    <View style={styles.rowWrap}>
      <Text style={styles.rail}>{time}</Text>
      <TouchableOpacity style={[styles.card, styles.cardRow]} onPress={onPress} activeOpacity={0.8}>
        <View style={styles.compWrap}>
          {isFavorite && <Icon name="star" size={14} color={COLORS.favorite} filled />}
          <Text style={styles.comp} numberOfLines={1}>{comp ?? ""}</Text>
        </View>
        <Text style={styles.title} numberOfLines={3}>{mainTitle}</Text>
        {footer}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 14,
    gap: 10,
  },
  cardLive: {
    borderColor: COLORS.accent,
    borderRadius: 20,
    padding: 16,
    gap: 14,
    marginBottom: 12,
  },
  cardRow: { flex: 1, minWidth: 0 },

  rowWrap: { flexDirection: "row", gap: 14, marginBottom: 12, alignItems: "stretch" },
  rail: {
    width: 64,
    fontFamily: FONTS.display,
    fontSize: 34,
    lineHeight: 36,
    color: COLORS.text,
    paddingTop: 12,
  },

  topRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  compWrap: { flexDirection: "row", alignItems: "center", gap: 6, flex: 1, minWidth: 0 },
  comp: {
    fontFamily: FONTS.bodySemi,
    fontSize: 12,
    letterSpacing: 0.6,
    textTransform: "uppercase",
    color: COLORS.textSecondary,
    flexShrink: 1,
  },
  liveBadge: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 6,
  },
  liveBadgeText: {
    fontFamily: FONTS.displayBold,
    fontSize: 15,
    letterSpacing: 1,
    color: COLORS.onAccent,
  },

  vsRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  side: { flex: 1, flexDirection: "row", alignItems: "center", gap: 10, minWidth: 0 },
  sideRight: { justifyContent: "flex-end" },
  sideName: {
    flexShrink: 1,
    fontFamily: FONTS.displayBold,
    fontSize: 25,
    lineHeight: 26,
    textTransform: "uppercase",
    color: COLORS.text,
  },
  vs: {
    fontFamily: FONTS.displaySemi,
    fontSize: 17,
    color: COLORS.textSecondary,
  },
  score: {
    fontFamily: FONTS.display,
    fontSize: 30,
    color: COLORS.accent,
  },
  soloTitle: {
    fontFamily: FONTS.displayBold,
    fontSize: 26,
    lineHeight: 27,
    textTransform: "uppercase",
    color: COLORS.text,
  },
  title: {
    fontFamily: FONTS.displayBold,
    fontSize: 25,
    lineHeight: 26,
    textTransform: "uppercase",
    color: COLORS.text,
  },

  footer: { flexDirection: "row", alignItems: "center", gap: 8 },
  tiles: { flexDirection: "row", alignItems: "center", gap: 6 },
  tile: {
    minWidth: 40,
    height: 26,
    paddingHorizontal: 7,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: COLORS.borderActive,
    alignItems: "center",
    justifyContent: "center",
  },
  tileText: { fontFamily: FONTS.displayBold, fontSize: 14, letterSpacing: 0.2 },
  more: { fontFamily: FONTS.bodySemi, fontSize: 12, color: COLORS.textSecondary },
  channelNames: {
    flex: 1,
    fontFamily: FONTS.body,
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  bell: { padding: 4 },
});
