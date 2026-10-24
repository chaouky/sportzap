/**
 * HomeScreen — Programme TV sport (direction « Night Match »)
 *
 * En-tête, jour, filtre de sport, puis le programme groupé par tranche
 * horaire : EN DIRECT, MATIN, APRÈS-MIDI, SOIRÉE.
 */
import React, { useState } from "react";
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  RefreshControl,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { SportType } from "../types";
import { SPORTS, COLORS, FONTS, generateDays } from "../constants";
import { EventCard } from "../components/EventCard";
import { Logo } from "../components/Logo";
import { Icon } from "../components/Icon";
import { useEvents, EventGroup } from "../hooks/useEvents";
import { useChannels } from "../hooks/useChannels";
import { useFavorites } from "../hooks/useFavorites";
import { useAlerts } from "../hooks/useAlerts";

const DAYS = generateDays(5);

const WEEKDAYS = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
const MONTHS = [
  "janvier", "février", "mars", "avril", "mai", "juin",
  "juillet", "août", "septembre", "octobre", "novembre", "décembre",
];

function dayTitle(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  const wd = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
  return `${WEEKDAYS[wd]} ${d} ${MONTHS[m - 1]}`;
}

export function HomeScreen() {
  const navigation = useNavigation<any>();
  const [selectedSport, setSelectedSport] = useState<SportType | "all">("all");
  const [selectedDay, setSelectedDay] = useState(0);
  const { selectedSlugs } = useChannels();
  const { matchEvent } = useFavorites();
  const { isAlerted, toggleAlert } = useAlerts();

  const { groups, loading, error, refresh } = useEvents({
    date: DAYS[selectedDay]?.iso,
    sport: selectedSport,
    channelSlugs: selectedSlugs,
  });

  const renderGroup = (group: EventGroup) => {
    const isLive = group.block === "EN DIRECT";
    return (
      <View key={group.block} style={styles.group}>
        <View style={styles.groupHeader}>
          {isLive && <View style={styles.liveDot} />}
          <Text style={[styles.groupLabel, isLive && styles.groupLabelLive]}>
            {group.block}
          </Text>
        </View>
        {group.events.map(event => (
          <EventCard
            key={event.id}
            event={event}
            isFavorite={matchEvent(event).length > 0}
            onPress={() => {
              // TODO: écran de détail
            }}
            onBellPress={() => toggleAlert(event)}
            isBellActive={isAlerted(event.id)}
          />
        ))}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={refresh} tintColor={COLORS.accent} />
        }
      >
        {/* ── Header ── */}
        <View style={styles.header}>
          <Logo size={36} />
          <TouchableOpacity
            style={styles.iconBtn}
            accessibilityLabel="Rechercher"
            onPress={() => navigation.navigate("Favoris")}
          >
            <Icon name="search" size={20} />
          </TouchableOpacity>
        </View>

        {/* ── Title ── */}
        <View style={styles.titleBlock}>
          <Text style={styles.title}>{dayTitle(DAYS[selectedDay].iso)}</Text>
          <TouchableOpacity
            style={styles.channelsLink}
            onPress={() => navigation.navigate("Chaînes")}
            accessibilityLabel="Modifier mes chaînes"
          >
            <Icon name="tv" size={16} color={COLORS.accent} />
            <Text style={styles.channelsLinkText}>Sur mes chaînes · modifier</Text>
          </TouchableOpacity>
        </View>

        {/* ── Days ── */}
        <View style={styles.dayRow}>
          {DAYS.map(day => {
            const active = selectedDay === day.key;
            return (
              <TouchableOpacity
                key={day.key}
                style={[styles.dayTab, active && styles.dayTabActive]}
                onPress={() => setSelectedDay(day.key)}
                accessibilityLabel={`Afficher le ${day.date}`}
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
                <Text style={[styles.sportLabel, active && styles.sportLabelActive]}>
                  {sport.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* ── Error ── */}
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryBtn} onPress={refresh}>
              <Icon name="refresh" size={16} color={COLORS.onAccent} />
              <Text style={styles.retryText}>Réessayer</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ── Events ── */}
        <View style={styles.eventsContainer}>
          {groups.length === 0 && !loading && !error ? (
            <View style={styles.empty}>
              <Icon name="calendar" size={40} color={COLORS.textTertiary} />
              <Text style={styles.emptyTitle}>Rien à voir sur tes chaînes</Text>
              <Text style={styles.emptyDesc}>
                Essaie un autre jour, un autre sport, ou ajoute des chaînes.
              </Text>
            </View>
          ) : (
            groups.map(renderGroup)
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 140 },

  header: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingHorizontal: 20, paddingTop: 12,
  },
  iconBtn: {
    width: 44, height: 44, borderRadius: 14,
    backgroundColor: COLORS.card,
    borderWidth: 1, borderColor: COLORS.border,
    alignItems: "center", justifyContent: "center",
  },

  titleBlock: { paddingHorizontal: 20, marginTop: 22 },
  title: {
    fontFamily: FONTS.display, fontSize: 46, lineHeight: 46,
    textTransform: "uppercase", color: COLORS.text,
  },
  channelsLink: {
    flexDirection: "row", alignItems: "center", gap: 8,
    minHeight: 44, alignSelf: "flex-start",
  },
  channelsLinkText: {
    fontFamily: FONTS.bodyMedium, fontSize: 15, color: COLORS.textSecondary,
  },

  dayRow: {
    flexDirection: "row", gap: 8,
    paddingHorizontal: 20, marginTop: 6,
  },
  dayTab: {
    flex: 1, minHeight: 60, paddingVertical: 8,
    borderRadius: 14, borderWidth: 1, borderColor: COLORS.border,
    backgroundColor: COLORS.card,
    alignItems: "center", justifyContent: "center",
  },
  dayTabActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  dayLabel: {
    fontFamily: FONTS.bodySemi, fontSize: 12, letterSpacing: 1.2,
    color: COLORS.text,
  },
  dayLabelActive: { color: COLORS.onAccent },
  dayDate: {
    fontFamily: FONTS.display, fontSize: 26, lineHeight: 28,
    color: COLORS.text,
  },
  dayDateActive: { color: COLORS.onAccent },

  sportRow: { gap: 8, paddingHorizontal: 20, paddingTop: 16, paddingBottom: 4 },
  sportPill: {
    paddingHorizontal: 18, minHeight: 44, borderRadius: 999,
    borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.card,
    alignItems: "center", justifyContent: "center",
  },
  sportPillActive: { backgroundColor: COLORS.text, borderColor: COLORS.text },
  sportLabel: { fontFamily: FONTS.bodySemi, fontSize: 15, color: COLORS.text },
  sportLabelActive: { color: COLORS.bg },

  errorBox: {
    marginHorizontal: 20, marginTop: 16, padding: 16, borderRadius: 16,
    backgroundColor: COLORS.card, borderWidth: 1, borderColor: COLORS.borderActive,
    alignItems: "center", gap: 12,
  },
  errorText: { fontFamily: FONTS.bodyMedium, fontSize: 15, color: COLORS.text },
  retryBtn: {
    flexDirection: "row", alignItems: "center", gap: 8,
    minHeight: 44, paddingHorizontal: 20, borderRadius: 14,
    backgroundColor: COLORS.accent,
  },
  retryText: { fontFamily: FONTS.displayBold, fontSize: 17, letterSpacing: 0.6, textTransform: "uppercase", color: COLORS.onAccent },

  eventsContainer: { paddingHorizontal: 20, paddingTop: 22 },
  group: { marginBottom: 14 },
  groupHeader: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 },
  liveDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: COLORS.accent },
  groupLabel: {
    fontFamily: FONTS.displayBold, fontSize: 17, letterSpacing: 2.6,
    color: COLORS.textSecondary,
  },
  groupLabelLive: { color: COLORS.accent },

  empty: { alignItems: "center", paddingVertical: 56, gap: 10 },
  emptyTitle: { fontFamily: FONTS.displayBold, fontSize: 22, textTransform: "uppercase", color: COLORS.text },
  emptyDesc: { fontFamily: FONTS.body, fontSize: 14, color: COLORS.textSecondary, textAlign: "center" },
});
