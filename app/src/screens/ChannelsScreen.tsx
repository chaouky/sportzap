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
  StyleSheet, SafeAreaView, Switch,
} from "react-native";
import { COLORS } from "../constants";
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
    <SafeAreaView style={styles.safe}>
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
            <Text style={styles.quickBtnOutlineText}>🆓  TNT seule</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.quickBtn, styles.quickBtnFilled]}
            onPress={selectAll}
          >
            <Text style={styles.quickBtnFilledText}>✦  Tout activer</Text>
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
                  <Text style={styles.groupIcon}>{group.icon}</Text>
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
                  {groupState === "all" && <Text style={styles.groupToggleCheck}>✓</Text>}
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
                        {selected && <Text style={styles.channelCheckMark}>✓</Text>}
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
  scrollContent: { paddingBottom: 120 },

  // Header
  header: { paddingHorizontal: 22, paddingTop: 8 },
  title: {
    fontSize: 36, fontWeight: "400",
    fontFamily: "InstrumentSerif",
    color: COLORS.text, letterSpacing: -1,
  },
  titleAccent: { fontStyle: "italic", color: COLORS.accent },
  subtitle: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono",
    letterSpacing: 1.5, marginTop: 4,
  },
  headerDesc: {
    fontSize: 14, color: COLORS.textSecondary,
    marginTop: 12, lineHeight: 20,
  },

  // Quick actions
  quickActions: {
    flexDirection: "row", gap: 8,
    paddingHorizontal: 22, marginTop: 20,
  },
  quickBtn: {
    flex: 1, paddingVertical: 12, borderRadius: 14,
    alignItems: "center",
  },
  quickBtnOutline: {
    borderWidth: 1.5, borderColor: "rgba(0,0,0,0.08)",
    backgroundColor: "#fff",
  },
  quickBtnOutlineText: {
    fontSize: 13, fontWeight: "600", color: COLORS.text,
    fontFamily: "DMMono",
  },
  quickBtnFilled: { backgroundColor: COLORS.text },
  quickBtnFilledText: {
    fontSize: 13, fontWeight: "600", color: COLORS.bg,
    fontFamily: "DMMono",
  },

  // Stats
  statsBar: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 22, marginTop: 20, marginBottom: 8,
  },
  statsText: {
    fontSize: 13, fontWeight: "600",
    fontFamily: "DMMono", color: COLORS.text,
  },
  statsDetail: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono",
  },

  // Groups
  group: { marginTop: 16, paddingHorizontal: 22 },
  groupHeader: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(0,0,0,0.04)",
  },
  groupHeaderLeft: {
    flexDirection: "row", alignItems: "center", gap: 12, flex: 1,
  },
  groupIcon: { fontSize: 22 },
  groupTitleRow: {
    flexDirection: "row", alignItems: "center", gap: 8,
  },
  groupTitle: {
    fontSize: 16, fontWeight: "400",
    fontFamily: "InstrumentSerif", color: COLORS.text,
  },
  groupDesc: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono", marginTop: 2,
    maxWidth: 240,
  },
  freeTag: {
    backgroundColor: "rgba(22,163,74,0.08)",
    paddingHorizontal: 6, paddingVertical: 2,
    borderRadius: 4,
  },
  freeTagText: {
    fontSize: 9, fontWeight: "700", color: "#16A34A",
    fontFamily: "DMMono", letterSpacing: 0.5,
  },
  groupToggle: {
    width: 28, height: 28, borderRadius: 8,
    borderWidth: 2, borderColor: "rgba(0,0,0,0.1)",
    alignItems: "center", justifyContent: "center",
  },
  groupToggleActive: {
    backgroundColor: COLORS.text, borderColor: COLORS.text,
  },
  groupTogglePartial: {
    backgroundColor: "rgba(0,0,0,0.06)", borderColor: "rgba(0,0,0,0.15)",
  },
  groupToggleCheck: {
    fontSize: 14, fontWeight: "700", color: "#fff",
  },
  groupToggleDash: {
    fontSize: 14, fontWeight: "700", color: "rgba(0,0,0,0.4)",
  },

  // Channels
  channelList: {
    backgroundColor: "#fff",
    borderRadius: 16,
    marginTop: 8,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.04)",
    overflow: "hidden",
  },
  channelRow: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12, paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(0,0,0,0.03)",
  },
  channelRowLast: { borderBottomWidth: 0 },
  channelLeft: {
    flexDirection: "row", alignItems: "center", gap: 12, flex: 1,
  },
  channelBadge: {
    width: 38, height: 26, borderRadius: 6,
    alignItems: "center", justifyContent: "center",
  },
  channelBadgeText: {
    fontSize: 10, fontWeight: "800",
    letterSpacing: -0.3,
  },
  channelName: {
    fontSize: 14, fontWeight: "500", color: COLORS.text,
  },
  channelNameInactive: { color: "rgba(0,0,0,0.3)" },
  channelSports: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono", marginTop: 1,
  },
  channelCheck: {
    width: 24, height: 24, borderRadius: 12,
    borderWidth: 2, borderColor: "rgba(0,0,0,0.1)",
    alignItems: "center", justifyContent: "center",
  },
  channelCheckActive: {
    backgroundColor: COLORS.accent, borderColor: COLORS.accent,
  },
  channelCheckMark: {
    fontSize: 12, fontWeight: "700", color: "#fff",
  },

  // Footer
  footer: {
    paddingHorizontal: 22, paddingTop: 24, paddingBottom: 40,
  },
  footerText: {
    fontSize: 12, color: COLORS.textTertiary,
    textAlign: "center", lineHeight: 18,
  },
});
