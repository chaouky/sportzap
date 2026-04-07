/**
 * EventCard — Single sport event card (Stacked editorial design)
 *
 * Handles all display variants:
 *   - Matchup (team1 vs team2) with avatars
 *   - Solo event (F1, cycling stages)
 *   - Live, upcoming, finished states
 */
import React from "react";
import {
  View, Text, TouchableOpacity, StyleSheet, Animated,
} from "react-native";
import { SportEvent } from "../types";
import { SPORTS, COLORS, getChannelBadge } from "../constants";
import { EntityAvatar } from "./EntityAvatar";
import { SportIcon } from "./SportIcon";

interface Props {
  event: SportEvent;
  onPress?: () => void;
  onBellPress?: () => void;
  isBellActive?: boolean;
  isFavorite?: boolean;
}

export function EventCard({ event, onPress, onBellPress, isBellActive, isFavorite }: Props) {
  const sportConfig = SPORTS.find(s => s.id === event.sport) || SPORTS[0];
  const channelBadge = getChannelBadge(event.channel.slug);
  const isLive = event.status === "live";
  const isDone = event.status === "finished";
  const hasScore = event.score1 != null;
  const isSolo = !event.team2;
  const isPlayerMatch = event.team1?.type === "player" || event.team2?.type === "player";

  return (
    <TouchableOpacity
      style={[
        styles.card,
        isLive && styles.cardLive,
        isFavorite && !isLive && { borderLeftWidth: 3, borderLeftColor: "#F59E0B" },
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {/* ── Header row ── */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={[styles.sportBadge, { backgroundColor: sportConfig.color + "12" }]}>
            <SportIcon sport={event.sport} color={sportConfig.color} size={14} />
          </View>
          <Text style={styles.competition}>{event.competition || "—"}</Text>
          {isFavorite && <Text style={{ fontSize: 10, color: "#F59E0B" }}>★</Text>}
        </View>

        {isLive && (
          <View style={styles.liveBadge}>
            <View style={styles.liveDot} />
            <Text style={styles.liveText}>DIRECT</Text>
          </View>
        )}
        {isDone && <Text style={styles.doneText}>FIN</Text>}
      </View>

      {/* ── Match content ── */}
      {isSolo ? (
        // Solo event (F1, cycling, etc.)
        <View style={styles.soloRow}>
          {event.team1 && <EntityAvatar entity={event.team1} size={40} />}
          <View style={{ marginLeft: event.team1 ? 14 : 0 }}>
            <Text style={styles.soloTitle}>{event.subtitle || event.title}</Text>
            {event.result && (
              <Text style={[styles.result, { color: sportConfig.color }]}>{event.result}</Text>
            )}
          </View>
        </View>
      ) : (
        // Matchup (team1 vs team2)
        <View style={styles.matchRow}>
          {/* Team 1 */}
          <View style={styles.teamSide}>
            <Text style={[styles.teamName, { textAlign: "right" }]} numberOfLines={2}>
              {isPlayerMatch && event.team1?.name ? event.team1.name : event.team1?.name || "?"}
            </Text>
            <EntityAvatar
              entity={event.team1}
              size={isPlayerMatch ? 42 : 36}
              side="left"
            />
          </View>

          {/* Score / Time */}
          <View style={styles.scoreCenter}>
            {hasScore ? (
              <View style={{ alignItems: "center" }}>
                <Text style={[styles.score, isLive && { color: COLORS.live }]}>
                  {event.score1}
                  <Text style={styles.scoreSep}> – </Text>
                  {event.score2}
                </Text>
                {event.minute && (
                  <Text style={styles.minute}>{event.minute}</Text>
                )}
              </View>
            ) : (
              <View style={styles.timePill}>
                <Text style={styles.timeText}>
                  {new Date(event.start).toLocaleTimeString("fr-FR", {
                    hour: "2-digit", minute: "2-digit",
                  })}
                </Text>
              </View>
            )}
          </View>

          {/* Team 2 */}
          <View style={[styles.teamSide, { flexDirection: "row" }]}>
            <EntityAvatar
              entity={event.team2}
              size={isPlayerMatch ? 42 : 36}
              side="right"
            />
            <Text style={[styles.teamName, { textAlign: "left" }]} numberOfLines={2}>
              {isPlayerMatch && event.team2?.name ? event.team2.name : event.team2?.name || "?"}
            </Text>
          </View>
        </View>
      )}

      {/* ── Footer ── */}
      <View style={styles.footer}>
        <View style={styles.footerLeft}>
          <View style={[styles.channelBadge, { backgroundColor: channelBadge.bg }]}>
            <Text style={[styles.channelLabel, { color: channelBadge.fg }]}>
              {channelBadge.label}
            </Text>
          </View>
          <Text style={styles.channelName}>{event.channel.name}</Text>
          {!event.channel.is_free && (
            <View style={styles.paidTag}>
              <Text style={styles.paidText}>PAYANT</Text>
            </View>
          )}
        </View>

        <View style={styles.footerRight}>
          {!hasScore && (
            <Text style={styles.footerTime}>
              {new Date(event.start).toLocaleTimeString("fr-FR", {
                hour: "2-digit", minute: "2-digit",
              })}
            </Text>
          )}
          <TouchableOpacity
            style={[
              styles.bellButton,
              isBellActive && { backgroundColor: sportConfig.color + "12" },
            ]}
            onPress={onBellPress}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={{ fontSize: 14, opacity: isBellActive ? 1 : 0.3 }}>🔔</Text>
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 8,
  },
  cardLive: {
    backgroundColor: COLORS.liveBg,
    borderColor: COLORS.liveBorder,
  },

  // Header
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  headerLeft: { flexDirection: "row", alignItems: "center", gap: 8 },
  sportBadge: {
    width: 26, height: 26, borderRadius: 7,
    alignItems: "center", justifyContent: "center",
  },
  competition: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono",
  },
  liveBadge: {
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(239,68,68,0.06)",
    paddingHorizontal: 10, paddingVertical: 3, borderRadius: 20,
  },
  liveDot: {
    width: 6, height: 6, borderRadius: 3,
    backgroundColor: COLORS.live,
  },
  liveText: {
    fontSize: 10, fontWeight: "600", color: COLORS.live,
    fontFamily: "DMMono", letterSpacing: 1,
  },
  doneText: {
    fontSize: 10, fontWeight: "500", color: COLORS.textTertiary,
    fontFamily: "DMMono",
  },

  // Solo
  soloRow: {
    flexDirection: "row", alignItems: "center",
    marginBottom: 12,
  },
  soloTitle: { fontSize: 17, fontWeight: "400", fontFamily: "InstrumentSerif" },
  result: { fontSize: 13, fontWeight: "500", marginTop: 2, fontFamily: "DMMono" },

  // Match
  matchRow: {
    flexDirection: "row", alignItems: "center",
    marginBottom: 12,
  },
  teamSide: {
    flex: 1, flexDirection: "row-reverse",
    alignItems: "center", gap: 10,
  },
  teamName: {
    fontSize: 15, fontWeight: "400",
    fontFamily: "InstrumentSerif",
    lineHeight: 18, flex: 1,
  },
  scoreCenter: {
    alignItems: "center", minWidth: 60,
    paddingHorizontal: 4,
  },
  score: {
    fontFamily: "DMMono", fontSize: 20, fontWeight: "500",
    color: COLORS.text, letterSpacing: 1,
  },
  scoreSep: { opacity: 0.2 },
  minute: {
    fontSize: 11, color: COLORS.live,
    fontFamily: "DMMono", marginTop: 1,
  },
  timePill: {
    backgroundColor: "rgba(0,0,0,0.03)",
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 8,
  },
  timeText: {
    fontFamily: "DMMono", fontSize: 14,
    fontWeight: "500", color: "rgba(0,0,0,0.4)",
  },

  // Footer
  footer: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center", paddingTop: 12,
    borderTopWidth: 1, borderTopColor: COLORS.border,
  },
  footerLeft: { flexDirection: "row", alignItems: "center", gap: 8 },
  channelBadge: {
    height: 22, borderRadius: 5,
    paddingHorizontal: 7,
    alignItems: "center", justifyContent: "center",
  },
  channelLabel: {
    fontSize: 9, fontWeight: "800",
    fontFamily: "system", letterSpacing: -0.2,
  },
  channelName: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono",
  },
  paidTag: {
    borderWidth: 1, borderColor: "rgba(0,0,0,0.08)",
    borderRadius: 4, paddingHorizontal: 5, paddingVertical: 1,
  },
  paidText: {
    fontSize: 8, fontWeight: "600", color: COLORS.textTertiary,
    fontFamily: "DMMono",
  },
  footerRight: { flexDirection: "row", alignItems: "center", gap: 8 },
  footerTime: {
    fontSize: 12, fontFamily: "DMMono",
    color: "rgba(0,0,0,0.22)",
  },
  bellButton: {
    width: 30, height: 30, borderRadius: 8,
    backgroundColor: "rgba(0,0,0,0.02)",
    alignItems: "center", justifyContent: "center",
  },
});
