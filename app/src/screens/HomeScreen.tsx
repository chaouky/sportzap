/**
 * HomeScreen — Main programme screen
 *
 * Layout (Stacked editorial design):
 *   Header: SportZap title + search
 *   Day tabs: AUJ. | LUN | MAR | ...
 *   Sport pills: Tout | Football | Rugby | ...
 *   Grouped events: EN DIRECT → MATIN → APRÈS-MIDI → SOIRÉE
 */
import React, { useState } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, RefreshControl, SafeAreaView, StatusBar,
} from "react-native";
import { SPORTS, COLORS, generateDays } from "../constants";
import { SportType } from "../types";
import { useEvents, EventGroup } from "../hooks/useEvents";
import { useChannels } from "../hooks/useChannels";
import { useFavorites } from "../hooks/useFavorites";
import { useAlerts } from "../hooks/useAlerts";
import { EventCard } from "../components/EventCard";
import { SportIcon } from "../components/SportIcon";

const DAYS = generateDays(5);

export function HomeScreen() {
  const [selectedSport, setSelectedSport] = useState<SportType | "all">("all");
  const [selectedDay, setSelectedDay] = useState(0);
  const { selectedSlugs } = useChannels();
  const { matchEvent } = useFavorites();
  const { isAlerted, toggleAlert } = useAlerts();

  const { groups, loading, error, refresh, liveCount } = useEvents({
    date: DAYS[selectedDay]?.iso,
    sport: selectedSport,
  });

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.bg} />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={refresh} tintColor={COLORS.text} />
        }
      >
        {/* ── Header ── */}
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>
              Sport<Text style={styles.titleAccent}>Zap</Text>
            </Text>
            <Text style={styles.subtitle}>PROGRAMME TV SPORT · FRANCE</Text>
          </View>
          <TouchableOpacity style={styles.searchBtn}>
            <Text style={{ fontSize: 16 }}>🔍</Text>
          </TouchableOpacity>
        </View>

        {/* ── Day tabs ── */}
        <View style={styles.dayRow}>
          {DAYS.map(day => {
            const active = selectedDay === day.key;
            return (
              <TouchableOpacity
                key={day.key}
                style={[styles.dayTab, active && styles.dayTabActive]}
                onPress={() => setSelectedDay(day.key)}
              >
                <Text style={[styles.dayLabel, active && styles.dayLabelActive]}>
                  {day.short}
                </Text>
                <Text style={[styles.dayDate, active && styles.dayDateActive]}>
                  {day.date}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* ── Sport filters ── */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.sportRow}
        >
          {SPORTS.map(sport => {
            const active = selectedSport === sport.id;
            return (
              <TouchableOpacity
                key={sport.id}
                style={[styles.sportPill, active && styles.sportPillActive]}
                onPress={() => setSelectedSport(sport.id as SportType | "all")}
              >
                {sport.id !== "all" && (
                  <SportIcon
                    sport={sport.id as SportType}
                    color={active ? "#F5F2ED" : "rgba(0,0,0,0.3)"}
                    size={14}
                  />
                )}
                <Text style={[styles.sportLabel, active && styles.sportLabelActive]}>
                  {sport.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* ── Error banner ── */}
        {error && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>⚡ {error}</Text>
          </View>
        )}

        {/* ── Event groups ── */}
        <View style={styles.eventsContainer}>
          {groups.length === 0 && !loading ? (
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>📭</Text>
              <Text style={styles.emptyTitle}>Aucun événement</Text>
              <Text style={styles.emptyDesc}>
                Essayez un autre jour ou d'autres filtres
              </Text>
            </View>
          ) : (
            groups.map(group => (
              <View key={group.block} style={styles.group}>
                {/* Section header */}
                <View style={styles.groupHeader}>
                  {group.block === "EN DIRECT" && <View style={styles.liveDot} />}
                  <Text style={[
                    styles.groupLabel,
                    group.block === "EN DIRECT" && { color: COLORS.live },
                  ]}>
                    {group.block}
                  </Text>
                  <View style={[
                    styles.groupLine,
                    group.block === "EN DIRECT" && { backgroundColor: "rgba(239,68,68,0.12)" },
                  ]} />
                </View>

                {/* Event cards */}
                {group.events.map(event => (
                  <EventCard
                    key={event.id}
                    event={event}
                    isFavorite={matchEvent(event).length > 0}
                    onPress={() => {
                      // TODO: navigate to detail screen
                    }}
                    onBellPress={() => toggleAlert(event)}
                    isBellActive={isAlerted(event.id)}
                  />
                ))}
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 100 },

  // Header
  header: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "flex-start",
    paddingHorizontal: 22, paddingTop: 8,
  },
  title: {
    fontSize: 36, fontWeight: "400",
    fontFamily: "InstrumentSerif",
    color: COLORS.text, letterSpacing: -1,
  },
  titleAccent: {
    fontStyle: "italic",
    color: COLORS.accent,
  },
  subtitle: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono",
    letterSpacing: 1.5, marginTop: 4,
  },
  searchBtn: {
    width: 36, height: 36, borderRadius: 20,
    borderWidth: 1.5, borderColor: "rgba(0,0,0,0.08)",
    backgroundColor: "#fff",
    alignItems: "center", justifyContent: "center",
    shadowColor: "#000", shadowOpacity: 0.03, shadowRadius: 3,
    elevation: 1,
  },

  // Days
  dayRow: {
    flexDirection: "row",
    marginHorizontal: 22, marginTop: 24,
    borderBottomWidth: 1.5, borderBottomColor: "rgba(0,0,0,0.06)",
  },
  dayTab: {
    flex: 1, alignItems: "center",
    paddingBottom: 12,
    borderBottomWidth: 2.5,
    borderBottomColor: "transparent",
    marginBottom: -1.5,
  },
  dayTabActive: { borderBottomColor: COLORS.text },
  dayLabel: {
    fontSize: 10, fontWeight: "500",
    color: "rgba(0,0,0,0.2)",
    fontFamily: "DMMono", letterSpacing: 1,
  },
  dayLabelActive: { color: COLORS.text },
  dayDate: {
    fontSize: 20, fontWeight: "400",
    color: "rgba(0,0,0,0.15)",
    fontFamily: "InstrumentSerif", marginTop: 2,
  },
  dayDateActive: { color: COLORS.text },

  // Sports
  sportRow: {
    flexDirection: "row", gap: 6,
    paddingHorizontal: 22, paddingTop: 20,
    paddingBottom: 6,
  },
  sportPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 14, paddingVertical: 7,
    borderRadius: 24,
    backgroundColor: "rgba(0,0,0,0.03)",
  },
  sportPillActive: { backgroundColor: COLORS.text },
  sportLabel: {
    fontSize: 12, fontWeight: "500",
    color: "rgba(0,0,0,0.35)",
    fontFamily: "DMMono",
  },
  sportLabelActive: { color: "#F5F2ED" },

  // Error
  errorBanner: {
    marginHorizontal: 22, marginTop: 12,
    padding: 10, borderRadius: 12,
    backgroundColor: "rgba(245,158,11,0.08)",
    borderWidth: 1, borderColor: "rgba(245,158,11,0.15)",
  },
  errorText: { fontSize: 12, color: "#D97706", fontFamily: "DMMono", textAlign: "center" },

  // Events
  eventsContainer: { paddingHorizontal: 22, paddingTop: 20 },

  // Groups
  group: { marginBottom: 28 },
  groupHeader: {
    flexDirection: "row", alignItems: "center",
    gap: 12, marginBottom: 14,
  },
  liveDot: {
    width: 8, height: 8, borderRadius: 4,
    backgroundColor: COLORS.live,
    shadowColor: COLORS.live, shadowOpacity: 0.5, shadowRadius: 4,
  },
  groupLabel: {
    fontSize: 11, fontWeight: "500",
    letterSpacing: 2.5,
    color: "rgba(0,0,0,0.28)",
    fontFamily: "DMMono",
  },
  groupLine: {
    flex: 1, height: 1,
    backgroundColor: "rgba(0,0,0,0.04)",
  },

  // Empty
  empty: {
    alignItems: "center", paddingVertical: 60,
  },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: {
    fontSize: 15, fontWeight: "600",
    color: "rgba(0,0,0,0.35)",
  },
  emptyDesc: {
    fontSize: 12, color: "rgba(0,0,0,0.2)",
    marginTop: 6,
  },
});
