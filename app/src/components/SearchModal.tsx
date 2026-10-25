/**
 * SearchModal — recherche plein écran dans tout le programme à venir
 * (tous les jours disponibles, pas seulement le jour affiché).
 */
import React, { useEffect, useMemo, useState } from "react";
import {
  Modal, View, Text, TextInput, ScrollView, TouchableOpacity, StyleSheet, Keyboard,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { SportEvent } from "../types";
import { COLORS, FONTS, kickoffOf, parisDateLabel } from "../constants";
import { fetchUpcomingEvents } from "../services/api";
import { mergeDuplicateEvents } from "../services/mergeEvents";
import { searchEvents } from "../services/search";
import { EventCard } from "./EventCard";
import { EventDetail } from "./EventDetail";
import { Icon } from "./Icon";
import { useFavorites } from "../hooks/useFavorites";
import { useAlerts } from "../hooks/useAlerts";

interface Props {
  visible: boolean;
  onClose: () => void;
  /** Chaînes choisies par l'utilisateur (« Mes chaînes »). */
  channelSlugs?: Set<string>;
}

export function SearchModal({ visible, onClose, channelSlugs }: Props) {
  const [query, setQuery] = useState("");
  const [all, setAll] = useState<SportEvent[]>([]);
  const [onlyMine, setOnlyMine] = useState(true);
  const [detail, setDetail] = useState<SportEvent | null>(null);
  const { matchEvent } = useFavorites();
  const { isAlerted, toggleAlert } = useAlerts();

  useEffect(() => {
    if (!visible) return;
    let alive = true;
    fetchUpcomingEvents().then(list => { if (alive) setAll(list); }).catch(() => {});
    return () => { alive = false; };
  }, [visible]);

  const sections = useMemo(() => {
    let pool = all;
    if (onlyMine && channelSlugs && channelSlugs.size > 0) {
      pool = pool.filter(e => channelSlugs.has(e.channel.slug));
    }
    const found = mergeDuplicateEvents(searchEvents(pool, query));
    const byDay = new Map<string, SportEvent[]>();
    for (const e of found) {
      const label = parisDateLabel(kickoffOf(e));
      if (!byDay.has(label)) byDay.set(label, []);
      byDay.get(label)!.push(e);
    }
    return [...byDay.entries()];
  }, [all, query, onlyMine, channelSlugs]);

  const close = () => { Keyboard.dismiss(); setDetail(null); onClose(); };
  const hasQuery = query.trim().length > 0;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={close}>
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        <View style={styles.bar}>
          <View style={styles.inputWrap}>
            <Icon name="search" size={18} color={COLORS.textSecondary} />
            <TextInput
              style={styles.input}
              value={query}
              onChangeText={setQuery}
              placeholder="Équipe, compétition, chaîne…"
              placeholderTextColor={COLORS.textTertiary}
              autoFocus
              autoCorrect={false}
              returnKeyType="search"
              selectionColor={COLORS.accent}
            />
            {hasQuery && (
              <TouchableOpacity onPress={() => setQuery("")} accessibilityLabel="Effacer" hitSlop={10}>
                <Icon name="close" size={16} color={COLORS.textSecondary} />
              </TouchableOpacity>
            )}
          </View>
          <TouchableOpacity onPress={close} style={styles.cancel} accessibilityLabel="Fermer la recherche">
            <Text style={styles.cancelText}>Annuler</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={[styles.scope, !onlyMine && styles.scopeAll]}
          onPress={() => setOnlyMine(v => !v)}
          accessibilityLabel="Basculer entre mes chaînes et toutes les chaînes"
        >
          <Icon name="tv" size={14} color={onlyMine ? COLORS.accent : COLORS.text} />
          <Text style={styles.scopeText}>{onlyMine ? "Sur mes chaînes" : "Toutes les chaînes"}</Text>
        </TouchableOpacity>

        <ScrollView
          contentContainerStyle={styles.list}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
        >
          {!hasQuery ? (
            <Text style={styles.hint}>Cherche une équipe, une compétition, un sport ou une chaîne.</Text>
          ) : sections.length === 0 ? (
            <Text style={styles.hint}>Aucun match à venir pour « {query.trim()} ».</Text>
          ) : (
            sections.map(([label, events]) => (
              <View key={label} style={styles.day}>
                <Text style={styles.dayLabel}>{label.toUpperCase()}</Text>
                {events.map(e => (
                  <EventCard
                    key={e.id}
                    event={e}
                    isFavorite={matchEvent(e).length > 0}
                    onPress={() => setDetail(e)}
                    onBellPress={() => toggleAlert(e)}
                    isBellActive={isAlerted(e.id)}
                  />
                ))}
              </View>
            ))
          )}
        </ScrollView>

        <EventDetail
          event={detail}
          onClose={() => setDetail(null)}
          isBellActive={detail ? isAlerted(detail.id) : false}
          onBellPress={detail ? () => toggleAlert(detail) : undefined}
        />
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  bar: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 16, paddingTop: 10 },
  inputWrap: {
    flex: 1, flexDirection: "row", alignItems: "center", gap: 10, minHeight: 48,
    paddingHorizontal: 14, borderRadius: 14, backgroundColor: COLORS.card,
    borderWidth: 1, borderColor: COLORS.borderActive,
  },
  input: { flex: 1, fontFamily: FONTS.bodyMedium, fontSize: 16, color: COLORS.text, paddingVertical: 8 },
  cancel: { minHeight: 44, justifyContent: "center", paddingHorizontal: 6 },
  cancelText: { fontFamily: FONTS.bodySemi, fontSize: 15, color: COLORS.accent },

  scope: {
    flexDirection: "row", alignItems: "center", gap: 8, alignSelf: "flex-start",
    minHeight: 44, marginLeft: 16, paddingHorizontal: 4,
  },
  scopeAll: { opacity: 0.9 },
  scopeText: { fontFamily: FONTS.bodyMedium, fontSize: 14, color: COLORS.textSecondary },

  list: { paddingHorizontal: 16, paddingBottom: 60 },
  hint: { fontFamily: FONTS.body, fontSize: 15, color: COLORS.textSecondary, textAlign: "center", paddingTop: 40 },
  day: { marginBottom: 14 },
  dayLabel: {
    fontFamily: FONTS.displayBold, fontSize: 16, letterSpacing: 2.2,
    color: COLORS.textSecondary, marginVertical: 10,
  },
});
