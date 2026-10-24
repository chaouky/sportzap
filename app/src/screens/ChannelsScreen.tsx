/**
 * ChannelsScreen — "Mes Chaînes"
 *
 * Lets the user select which channels they receive.
 * Grouped by bouquet (TNT, Canal+, beIN, DAZN...).
 * Each group has a master toggle + individual channel toggles.
 *
 * Design: Stacked editorial, same visual language as HomeScreen.
 */
import React from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { COLORS, FONTS } from "../constants";
import { Icon } from "../components/Icon";
import {
  CHANNEL_GROUPS,
  ALL_CHANNELS,
  ChannelGroup,
  getChannelsByGroup,
} from "../constants/channels";
import { useChannels } from "../hooks/useChannels";

export function ChannelsScreen() {
  const {
    toggle,
    toggleGroup,
    selectAll,
    selectFreeOnly,
    isGroupSelected,
    isSelected,
    stats,
  } = useChannels();

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Header ── */}
        <View style={styles.header}>
          <Text style={styles.title}>
            Mes <Text style={styles.titleAccent}>Chaînes</Text>
          </Text>
          <Text style={styles.subtitle}>
            SÉLECTIONNEZ LES CHAÎNES QUE VOUS RECEVEZ
          </Text>
          <Text style={styles.headerDesc}>
            SportZap n'affichera que les événements diffusés sur vos chaînes.
          </Text>
        </View>

        {/* ── Quick actions ── */}
        <View style={styles.quickActions}>
          <TouchableOpacity
            style={[styles.quickBtn, styles.quickBtnOutline]}
            onPress={selectFreeOnly}
          >
            <Text style={styles.quickBtnOutlineText}>TNT seule</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.quickBtn, styles.quickBtnFilled]}
            onPress={selectAll}
          >
            <Text style={styles.quickBtnFilledText}>Tout activer</Text>
          </TouchableOpacity>
        </View>

        {/* ── Stats bar ── */}
        <View style={styles.statsBar}>
          <Text style={styles.statsText}>
            {stats.selected}/{stats.total} chaînes
          </Text>
          <Text style={styles.statsDetail}>
            {stats.freeSelected} gratuites · {stats.paidSelected} payantes
          </Text>
        </View>

        {/* ── Channel groups ── */}
        {CHANNEL_GROUPS.map(group => {
          const channels = getChannelsByGroup(group.id);
          const groupState = isGroupSelected(group.id);

          return (
            <View key={group.id} style={styles.group}>
              {/* Group header */}
              <TouchableOpacity
                style={styles.groupHeader}
                onPress={() => toggleGroup(group.id)}
                activeOpacity={0.7}
              >
                <View style={styles.groupHeaderLeft}>
                  <View>
                    <View style={styles.groupTitleRow}>
                      <Text style={styles.groupTitle}>{group.label}</Text>
                      {group.isFree && (
                        <View style={styles.freeTag}>
                          <Text style={styles.freeTagText}>GRATUIT</Text>
                        </View>
                      )}
                    </View>
                    <Text style={styles.groupDesc}>{group.description}</Text>
                  </View>
                </View>
                <View style={[
                  styles.groupToggle,
                  groupState === "all" && styles.groupToggleActive,
                  groupState === "some" && styles.groupTogglePartial,
                ]}>
                  {groupState === "all" && <Icon name="check" size={16} color={COLORS.onAccent} strokeWidth={3} />}
                  {groupState === "some" && <Text style={styles.groupToggleDash}>—</Text>}
                </View>
              </TouchableOpacity>

              {/* Individual channels */}
              <View style={styles.channelList}>
                {channels.map((ch, i) => {
                  const selected = isSelected(ch.slug);
                  return (
                    <TouchableOpacity
                      key={ch.slug}
                      style={[
                        styles.channelRow,
                        i === channels.length - 1 && styles.channelRowLast,
                      ]}
                      onPress={() => toggle(ch.slug)}
                      activeOpacity={0.7}
                    >
                      <View style={styles.channelLeft}>
                        <View style={[styles.channelBadge, {
                          backgroundColor: ch.badge.bg,
                          opacity: selected ? 1 : 0.35,
                        }]}>
                          <Text style={[styles.channelBadgeText, {
                            color: ch.badge.fg,
                          }]}>
                            {ch.badge.label}
                          </Text>
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={[
                            styles.channelName,
                            !selected && styles.channelNameInactive,
                          ]}>
                            {ch.name}
                          </Text>
                          <Text style={styles.channelSports}>{ch.sports}</Text>
                        </View>
                      </View>
                      <View style={[
                        styles.channelCheck,
                        selected && styles.channelCheckActive,
                      ]}>
                        {selected && <Icon name="check" size={14} color={COLORS.onAccent} strokeWidth={3} />}
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          );
        })}

        {/* ── Footer note ── */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Vous pouvez modifier votre sélection à tout moment.{"\n"}
            Les chaînes non sélectionnées masquent les événements correspondants.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 140 },

  // Header
  header: { paddingHorizontal: 20, paddingTop: 12 },
  title: {
    fontFamily: FONTS.display, fontSize: 46, lineHeight: 46,
    textTransform: "uppercase", color: COLORS.text,
  },
  titleAccent: { color: COLORS.accent },
  subtitle: {
    fontFamily: FONTS.bodySemi, fontSize: 12, letterSpacing: 1.2,
    color: COLORS.textSecondary, marginTop: 6,
  },
  headerDesc: {
    fontFamily: FONTS.body, fontSize: 15, color: COLORS.textSecondary,
    marginTop: 10, lineHeight: 21,
  },

  // Quick actions
  quickActions: {
    flexDirection: "row", gap: 8,
    paddingHorizontal: 20, marginTop: 20,
  },
  quickBtn: {
    flex: 1, minHeight: 48, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
  },
  quickBtnOutline: {
    borderWidth: 1, borderColor: COLORS.borderActive,
    backgroundColor: COLORS.card,
  },
  quickBtnOutlineText: {
    fontFamily: FONTS.displayBold, fontSize: 17, letterSpacing: 0.6,
    textTransform: "uppercase", color: COLORS.text,
  },
  quickBtnFilled: { backgroundColor: COLORS.accent },
  quickBtnFilledText: {
    fontFamily: FONTS.displayBold, fontSize: 17, letterSpacing: 0.6,
    textTransform: "uppercase", color: COLORS.onAccent,
  },

  // Stats
  statsBar: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20, marginTop: 20, marginBottom: 8,
  },
  statsText: { fontFamily: FONTS.displayBold, fontSize: 18, color: COLORS.text },
  statsDetail: { fontFamily: FONTS.body, fontSize: 13, color: COLORS.textSecondary },

  // Groups
  group: { marginTop: 16, paddingHorizontal: 20 },
  groupHeader: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  groupHeaderLeft: {
    flexDirection: "row", alignItems: "center", gap: 12, flex: 1,
  },
  groupIcon: { fontSize: 22 },
  groupTitleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  groupTitle: {
    fontFamily: FONTS.displayBold, fontSize: 22, letterSpacing: 0.4,
    textTransform: "uppercase", color: COLORS.text,
  },
  groupDesc: {
    fontFamily: FONTS.body, fontSize: 13, color: COLORS.textSecondary,
    marginTop: 2, maxWidth: 260,
  },
  freeTag: {
    backgroundColor: "rgba(200,255,46,0.14)",
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 5,
  },
  freeTagText: {
    fontFamily: FONTS.displayBold, fontSize: 12, letterSpacing: 1,
    color: COLORS.accent,
  },
  groupToggle: {
    width: 28, height: 28, borderRadius: 8,
    borderWidth: 2, borderColor: COLORS.borderActive,
    alignItems: "center", justifyContent: "center",
  },
  groupToggleActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  groupTogglePartial: { backgroundColor: COLORS.surface2, borderColor: COLORS.borderActive },
  groupToggleCheck: { fontSize: 14, color: COLORS.onAccent },
  groupToggleDash: { fontFamily: FONTS.bodySemi, fontSize: 14, color: COLORS.textSecondary },

  // Channels
  channelList: {
    backgroundColor: COLORS.card, borderRadius: 18, marginTop: 8,
    borderWidth: 1, borderColor: COLORS.border, overflow: "hidden",
  },
  channelRow: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12, paddingHorizontal: 14,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  channelRowLast: { borderBottomWidth: 0 },
  channelLeft: { flexDirection: "row", alignItems: "center", gap: 12, flex: 1 },
  channelBadge: {
    width: 46, height: 28, borderRadius: 7,
    borderWidth: 1, borderColor: COLORS.borderActive,
    alignItems: "center", justifyContent: "center",
  },
  channelBadgeText: { fontFamily: FONTS.displayBold, fontSize: 14 },
  channelName: { fontFamily: FONTS.bodySemi, fontSize: 15, color: COLORS.text },
  channelNameInactive: { color: COLORS.textTertiary },
  channelSports: {
    fontFamily: FONTS.body, fontSize: 12, color: COLORS.textSecondary, marginTop: 1,
  },
  channelCheck: {
    width: 26, height: 26, borderRadius: 13,
    borderWidth: 2, borderColor: COLORS.borderActive,
    alignItems: "center", justifyContent: "center",
  },
  channelCheckActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  channelCheckMark: { fontSize: 12, color: COLORS.onAccent },

  // Footer
  footer: { paddingHorizontal: 20, paddingTop: 24, paddingBottom: 40 },
  footerText: {
    fontFamily: FONTS.body, fontSize: 13, color: COLORS.textTertiary,
    textAlign: "center", lineHeight: 19,
  },
});
