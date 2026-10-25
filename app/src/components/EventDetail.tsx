/**
 * EventDetail — fiche d'un match (feuille qui monte du bas).
 *
 * Coup d'envoi officiel, heure de début de diffusion si elle diffère,
 * toutes les chaînes (logo + nom, gratuit / payant) et rappel.
 */
import React from "react";
import { Modal, View, Text, ScrollView, TouchableOpacity, Pressable, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Channel, SportEvent } from "../types";
import { COLORS, FONTS, kickoffOf, parisTime, parisDateLabel } from "../constants";
import { describeEvent } from "../services/describeEvent";
import { EntityAvatar } from "./EntityAvatar";
import { ChannelTile } from "./EventCard";
import { Icon } from "./Icon";
import { SportGlyph } from "./SportGlyph";

interface Props {
  event: SportEvent | null;
  onClose: () => void;
  isBellActive?: boolean;
  onBellPress?: () => void;
}

function uniqueChannels(event: SportEvent): Channel[] {
  const list = event.channels && event.channels.length > 0 ? event.channels : [event.channel];
  return list.filter(c => c.slug !== "a-confirmer");
}

export function EventDetail({ event, onClose, isBellActive, onBellPress }: Props) {
  return (
    <Modal
      visible={!!event}
      animationType="slide"
      transparent
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <Pressable style={styles.backdrop} onPress={onClose} accessibilityLabel="Fermer" />
      {event && <Sheet event={event} onClose={onClose} isBellActive={isBellActive} onBellPress={onBellPress} />}
    </Modal>
  );
}

function Sheet({ event, onClose, isBellActive, onBellPress }: Props & { event: SportEvent }) {
  const info = describeEvent(event);
  const hasTeams = !!(event.team1 && event.team2);
  const kickoff = kickoffOf(event);
  const channels = uniqueChannels(event);
  const isLive = event.status === "live";
  const hasKickoffGap = !!event.kickoff && parisTime(event.start) !== parisTime(event.kickoff);

  return (
    <SafeAreaView style={styles.sheetWrap} edges={["bottom"]} pointerEvents="box-none">
      <View style={styles.sheet}>
        <View style={styles.handle} />
        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
          <View style={styles.topRow}>
            <View style={styles.sportRow}>
              <SportGlyph name={info.glyph} size={20} color={COLORS.textSecondary} />
              <Text style={styles.sportText} numberOfLines={2}>
                <Text style={styles.sportName}>{info.sportLabel}</Text>
                {info.context ? ` · ${info.context}` : ""}
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn} accessibilityLabel="Fermer">
              <Icon name="close" size={18} />
            </TouchableOpacity>
          </View>

          {hasTeams ? (
            <View style={styles.vsRow}>
              <View style={styles.side}>
                <EntityAvatar entity={event.team1} size={56} />
                <Text style={styles.sideName} numberOfLines={2}>{event.team1!.name}</Text>
              </View>
              <Text style={styles.vs}>VS</Text>
              <View style={styles.side}>
                <EntityAvatar entity={event.team2} size={56} />
                <Text style={styles.sideName} numberOfLines={2}>{event.team2!.name}</Text>
              </View>
            </View>
          ) : (
            <Text style={styles.headline}>{info.headline}</Text>
          )}

          <View style={styles.whenBox}>
            <View style={{ flex: 1 }}>
              <Text style={styles.whenDay}>{upperFirst(parisDateLabel(kickoff))}</Text>
              <Text style={styles.whenLabel}>
                {isLive ? "Commencé à" : "Coup d'envoi"}
              </Text>
            </View>
            <Text style={[styles.whenTime, isLive && { color: COLORS.accent }]} allowFontScaling={false}>
              {parisTime(kickoff)}
            </Text>
          </View>
          {hasKickoffGap && (
            <Text style={styles.note}>
              Début de l'émission à {parisTime(event.start)}, avant-match inclus.
            </Text>
          )}

          <Text style={styles.sectionLabel}>OÙ LE REGARDER</Text>
          {channels.length === 0 ? (
            <Text style={styles.pending}>Diffuseur à confirmer</Text>
          ) : (
            channels.map(c => (
              <View key={c.name} style={styles.channelRow}>
                <ChannelTile channel={c} />
                <Text style={styles.channelName} numberOfLines={1}>{c.name}</Text>
                <Text style={[styles.channelTag, c.is_free && styles.channelTagFree]}>
                  {c.is_free ? "GRATUIT" : "ABONNEMENT"}
                </Text>
              </View>
            ))
          )}

          {!!event.description && (
            <>
              <Text style={styles.sectionLabel}>À PROPOS</Text>
              <Text style={styles.desc}>{event.description}</Text>
            </>
          )}

          {onBellPress && (
            <TouchableOpacity
              style={[styles.bellBtn, isBellActive && styles.bellBtnActive]}
              onPress={onBellPress}
              accessibilityLabel={isBellActive ? "Retirer le rappel" : "Me rappeler ce match"}
            >
              <Icon name="bell" size={18} color={isBellActive ? COLORS.onAccent : COLORS.text} filled={!!isBellActive} />
              <Text style={[styles.bellText, isBellActive && { color: COLORS.onAccent }]}>
                {isBellActive ? "Rappel activé" : "Me le rappeler"}
              </Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

/** « samedi 24 octobre » → « Samedi 24 octobre » (pas « Octobre » : textTransform capitaliserait chaque mot). */
const upperFirst = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(4,6,14,0.6)" },
  sheetWrap: { position: "absolute", left: 0, right: 0, bottom: 0, maxHeight: "86%" },
  sheet: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: 28, borderTopRightRadius: 28,
    borderWidth: 1, borderBottomWidth: 0, borderColor: COLORS.borderActive,
    paddingTop: 10,
  },
  handle: { alignSelf: "center", width: 44, height: 5, borderRadius: 3, backgroundColor: COLORS.borderActive },
  content: { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 24, gap: 14 },

  topRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 12 },
  sportRow: { flexDirection: "row", alignItems: "center", gap: 8, flexShrink: 1 },
  sportText: {
    flexShrink: 1, fontFamily: FONTS.bodyMedium, fontSize: 13, letterSpacing: 0.6,
    textTransform: "uppercase", color: COLORS.textSecondary,
  },
  sportName: { fontFamily: FONTS.bodySemi, color: COLORS.text },
  closeBtn: {
    width: 44, height: 44, borderRadius: 14, backgroundColor: COLORS.surface2,
    alignItems: "center", justifyContent: "center",
  },

  vsRow: { flexDirection: "row", alignItems: "flex-start", paddingVertical: 4 },
  side: { flex: 1, alignItems: "center", gap: 8, minWidth: 0 },
  sideName: {
    alignSelf: "stretch", textAlign: "center", fontFamily: FONTS.displayBold, fontSize: 24,
    lineHeight: 26, textTransform: "uppercase", color: COLORS.text,
  },
  vs: { width: 48, marginTop: 16, textAlign: "center", fontFamily: FONTS.displaySemi, fontSize: 18, color: COLORS.textSecondary },
  headline: {
    fontFamily: FONTS.displayBold, fontSize: 32, lineHeight: 34,
    textTransform: "uppercase", color: COLORS.text,
  },

  whenBox: {
    flexDirection: "row", alignItems: "center", padding: 14, borderRadius: 16,
    backgroundColor: COLORS.surface2,
  },
  whenDay: { fontFamily: FONTS.bodySemi, fontSize: 16, color: COLORS.text },
  whenLabel: { fontFamily: FONTS.body, fontSize: 13, color: COLORS.textSecondary, marginTop: 2 },
  whenTime: { fontFamily: FONTS.display, fontSize: 40, lineHeight: 42, color: COLORS.text },
  note: { fontFamily: FONTS.body, fontSize: 13, color: COLORS.textSecondary, marginTop: -6 },

  sectionLabel: {
    fontFamily: FONTS.displayBold, fontSize: 15, letterSpacing: 2.4,
    color: COLORS.textSecondary, marginTop: 4,
  },
  channelRow: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 36 },
  channelName: { flex: 1, fontFamily: FONTS.bodyMedium, fontSize: 15, color: COLORS.text },
  channelTag: { fontFamily: FONTS.bodySemi, fontSize: 11, letterSpacing: 1, color: COLORS.textTertiary },
  channelTagFree: { color: COLORS.accent },
  pending: { fontFamily: FONTS.bodyMedium, fontStyle: "italic", fontSize: 15, color: COLORS.textTertiary },
  desc: { fontFamily: FONTS.body, fontSize: 15, lineHeight: 21, color: COLORS.textSecondary },

  bellBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10,
    minHeight: 48, borderRadius: 14, borderWidth: 1, borderColor: COLORS.borderActive, marginTop: 6,
  },
  bellBtnActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  bellText: { fontFamily: FONTS.displayBold, fontSize: 18, letterSpacing: 0.6, textTransform: "uppercase", color: COLORS.text },
});
