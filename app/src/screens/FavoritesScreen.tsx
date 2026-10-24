/**
 * FavoritesScreen — "Mes Favoris"
 *
 * Two sections:
 *   1. "Mes suivis" — currently followed items with quick unfollow
 *   2. "Découvrir" — browse teams + competitions to follow
 *
 * Searchable. Grouped by sport.
 * Design: Stacked editorial.
 */
import React, { useState, useMemo } from "react";
import {
  View, Text, ScrollView, TouchableOpacity, TextInput,
  StyleSheet, Image,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { COLORS, FONTS } from "../constants";
import { Icon } from "../components/Icon";
import { COMPETITIONS, POPULAR_TEAMS, Followable } from "../constants/favorites";
import { useFavorites } from "../hooks/useFavorites";

const SPORT_SECTIONS = [
  { sport: "football", label: "Football", icon: "⚽" },
  { sport: "rugby", label: "Rugby", icon: "🏉" },
  { sport: "tennis", label: "Tennis", icon: "🎾" },
  { sport: "basket", label: "Basket", icon: "🏀" },
  { sport: "f1", label: "F1", icon: "🏎" },
  { sport: "mma", label: "MMA", icon: "🥊" },
  { sport: "cyclisme", label: "Cyclisme", icon: "🚴" },
  { sport: "handball", label: "Handball", icon: "🤾" },
];

function FollowableRow({ item, isFollowed, onToggle }: {
  item: Followable;
  isFollowed: boolean;
  onToggle: () => void;
}) {
  return (
    <TouchableOpacity
      style={[styles.itemRow, isFollowed && styles.itemRowFollowed]}
      onPress={onToggle}
      activeOpacity={0.7}
    >
      <View style={styles.itemLeft}>
        {/* Avatar */}
        {item.logoUrl ? (
          <View style={[styles.itemAvatar, styles.itemAvatarLogo]}>
            <Image source={{ uri: item.logoUrl }} style={{ width: 24, height: 24 }} resizeMode="contain" />
          </View>
        ) : item.flagCode ? (
          <View style={[styles.itemAvatar, { overflow: "hidden" }]}>
            <Image source={{ uri: `https://flagcdn.com/w80/${item.flagCode}.png` }} style={{ width: 38, height: 38 }} resizeMode="cover" />
          </View>
        ) : (
          <View style={[styles.itemAvatar, styles.itemAvatarMono]}>
            <Text style={styles.itemAvatarText}>{item.short.slice(0, 3)}</Text>
          </View>
        )}

        <View style={{ flex: 1 }}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={styles.itemMeta}>
            {item.type === "competition" ? "Compétition" : "Équipe"} · {item.sport}
          </Text>
        </View>
      </View>

      <View style={[
        styles.followBtn,
        isFollowed ? styles.followBtnActive : styles.followBtnInactive,
      ]}>
        <Text style={[
          styles.followBtnText,
          isFollowed ? styles.followBtnTextActive : styles.followBtnTextInactive,
        ]}>
          {isFollowed ? "✓ Suivi" : "+ Suivre"}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

export function FavoritesScreen() {
  const { isFollowing, toggle, followedTeams, followedCompetitions, stats } = useFavorites();
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<"following" | "discover">(
    stats.totalFollowed > 0 ? "following" : "discover"
  );

  // All followables
  const allItems = useMemo(() => [...COMPETITIONS, ...POPULAR_TEAMS], []);

  // Search filter
  const filteredItems = useMemo(() => {
    if (!search.trim()) return allItems;
    const q = search.toLowerCase();
    return allItems.filter(item =>
      item.name.toLowerCase().includes(q) ||
      item.short.toLowerCase().includes(q) ||
      item.aliases.some(a => a.toLowerCase().includes(q))
    );
  }, [search, allItems]);

  // Followed items
  const followedItems = useMemo(() =>
    allItems.filter(item => isFollowing(item.id)),
    [allItems, isFollowing]
  );

  // Group by sport
  const groupedDiscover = useMemo(() => {
    const groups: { sport: string; label: string; icon: string; comps: Followable[]; teams: Followable[] }[] = [];
    for (const section of SPORT_SECTIONS) {
      const comps = filteredItems.filter(i => i.type === "competition" && i.sport === section.sport);
      const teams = filteredItems.filter(i => i.type === "team" && i.sport === section.sport);
      if (comps.length > 0 || teams.length > 0) {
        groups.push({ ...section, comps, teams });
      }
    }
    return groups;
  }, [filteredItems]);

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── Header ── */}
        <View style={styles.header}>
          <Text style={styles.title}>
            Mes <Text style={styles.titleAccent}>Favoris</Text>
          </Text>
          <Text style={styles.subtitle}>
            SUIVEZ VOS ÉQUIPES ET COMPÉTITIONS
          </Text>
        </View>

        {/* ── Search ── */}
        <View style={styles.searchContainer}>
          <View style={styles.searchIcon}><Icon name="search" size={18} color={COLORS.textSecondary} /></View>
          <TextInput
            style={styles.searchInput}
            placeholder="Rechercher une équipe, une compétition..."
            placeholderTextColor={COLORS.textTertiary}
            selectionColor={COLORS.accent}
            value={search}
            onChangeText={setSearch}
            onFocus={() => setActiveTab("discover")}
          />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => setSearch("")}>
              <View style={styles.searchClear}><Icon name="close" size={18} color={COLORS.textSecondary} /></View>
            </TouchableOpacity>
          )}
        </View>

        {/* ── Tabs ── */}
        {!search && (
          <View style={styles.tabs}>
            <TouchableOpacity
              style={[styles.tab, activeTab === "following" && styles.tabActive]}
              onPress={() => setActiveTab("following")}
            >
              <Text style={[styles.tabText, activeTab === "following" && styles.tabTextActive]}>
                Mes suivis ({stats.totalFollowed})
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.tab, activeTab === "discover" && styles.tabActive]}
              onPress={() => setActiveTab("discover")}
            >
              <Text style={[styles.tabText, activeTab === "discover" && styles.tabTextActive]}>
                Découvrir
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ── Content ── */}
        {(activeTab === "following" && !search) ? (
          // MY FOLLOWS
          <View style={styles.content}>
            {followedItems.length === 0 ? (
              <View style={styles.empty}>
                <Icon name="star" size={40} color={COLORS.textTertiary} />
                <Text style={styles.emptyTitle}>Aucun favori</Text>
                <Text style={styles.emptyDesc}>
                  Suivez des équipes et compétitions pour retrouver{"\n"}leurs événements en priorité.
                </Text>
                <TouchableOpacity
                  style={styles.emptyBtn}
                  onPress={() => setActiveTab("discover")}
                >
                  <Text style={styles.emptyBtnText}>Découvrir →</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                {/* Followed competitions */}
                {followedCompetitions.length > 0 && (
                  <View style={styles.section}>
                    <Text style={styles.sectionLabel}>COMPÉTITIONS</Text>
                    <View style={styles.card}>
                      {followedCompetitions.map(item => (
                        <FollowableRow
                          key={item.id}
                          item={item}
                          isFollowed={true}
                          onToggle={() => toggle(item.id)}
                        />
                      ))}
                    </View>
                  </View>
                )}

                {/* Followed teams */}
                {followedTeams.length > 0 && (
                  <View style={styles.section}>
                    <Text style={styles.sectionLabel}>ÉQUIPES</Text>
                    <View style={styles.card}>
                      {followedTeams.map(item => (
                        <FollowableRow
                          key={item.id}
                          item={item}
                          isFollowed={true}
                          onToggle={() => toggle(item.id)}
                        />
                      ))}
                    </View>
                  </View>
                )}
              </>
            )}
          </View>
        ) : (
          // DISCOVER / SEARCH RESULTS
          <View style={styles.content}>
            {search && filteredItems.length === 0 ? (
              <View style={styles.empty}>
                <Icon name="search" size={40} color={COLORS.textTertiary} />
                <Text style={styles.emptyTitle}>Aucun résultat</Text>
                <Text style={styles.emptyDesc}>
                  Essayez un autre terme de recherche
                </Text>
              </View>
            ) : (
              groupedDiscover.map(group => (
                <View key={group.sport} style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Text style={styles.sectionLabel}>{group.label.toUpperCase()}</Text>
                    <View style={styles.sectionLine} />
                  </View>

                  {/* Competitions */}
                  {group.comps.length > 0 && (
                    <View style={styles.card}>
                      {group.comps.map(item => (
                        <FollowableRow
                          key={item.id}
                          item={item}
                          isFollowed={isFollowing(item.id)}
                          onToggle={() => toggle(item.id)}
                        />
                      ))}
                    </View>
                  )}

                  {/* Teams */}
                  {group.teams.length > 0 && (
                    <View style={[styles.card, { marginTop: 8 }]}>
                      {group.teams.map(item => (
                        <FollowableRow
                          key={item.id}
                          item={item}
                          isFollowed={isFollowing(item.id)}
                          onToggle={() => toggle(item.id)}
                        />
                      ))}
                    </View>
                  )}
                </View>
              ))
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 140 },

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

  // Search
  searchContainer: {
    flexDirection: "row", alignItems: "center",
    backgroundColor: COLORS.card,
    borderRadius: 14, borderWidth: 1, borderColor: COLORS.border,
    marginHorizontal: 20, marginTop: 20,
    paddingHorizontal: 14, height: 48,
  },
  searchIcon: { marginRight: 10 },
  searchInput: {
    flex: 1, fontSize: 15, color: COLORS.text, fontFamily: FONTS.bodyMedium,
  },
  searchClear: { padding: 4 },

  // Tabs
  tabs: {
    flexDirection: "row", marginHorizontal: 20, marginTop: 20,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  tab: {
    minHeight: 44, justifyContent: "center", marginRight: 24,
    borderBottomWidth: 3, borderBottomColor: "transparent", marginBottom: -1,
  },
  tabActive: { borderBottomColor: COLORS.accent },
  tabText: { fontFamily: FONTS.bodySemi, fontSize: 15, color: COLORS.textSecondary },
  tabTextActive: { color: COLORS.text },

  // Content
  content: { paddingHorizontal: 20, paddingTop: 20 },

  // Sections
  section: { marginBottom: 24 },
  sectionHeader: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 12 },
  sectionIcon: { fontSize: 14 },
  sectionLabel: {
    fontFamily: FONTS.displayBold, fontSize: 17, letterSpacing: 2.6,
    color: COLORS.textSecondary,
  },
  sectionLine: { flex: 1, height: 1, backgroundColor: COLORS.border },

  // Card container
  card: {
    backgroundColor: COLORS.card, borderRadius: 18,
    borderWidth: 1, borderColor: COLORS.border, overflow: "hidden",
  },

  // Item rows
  itemRow: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingVertical: 12, paddingHorizontal: 14,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  itemRowFollowed: {},
  itemLeft: { flexDirection: "row", alignItems: "center", gap: 12, flex: 1 },
  itemAvatar: {
    width: 38, height: 38, borderRadius: 19,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: COLORS.border,
  },
  itemAvatarLogo: { backgroundColor: COLORS.text, borderColor: COLORS.text },
  itemAvatarMono: { backgroundColor: COLORS.surface2 },
  itemAvatarText: { fontFamily: FONTS.displayBold, fontSize: 13, color: COLORS.text },
  itemName: { fontFamily: FONTS.bodySemi, fontSize: 15, color: COLORS.text },
  itemMeta: {
    fontFamily: FONTS.body, fontSize: 12, color: COLORS.textSecondary, marginTop: 1,
  },

  // Follow button
  followBtn: {
    minHeight: 36, paddingHorizontal: 14, justifyContent: "center",
    borderRadius: 20, borderWidth: 1,
  },
  followBtnActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  followBtnInactive: { backgroundColor: "transparent", borderColor: COLORS.borderActive },
  followBtnText: { fontFamily: FONTS.bodySemi, fontSize: 13 },
  followBtnTextActive: { color: COLORS.onAccent },
  followBtnTextInactive: { color: COLORS.text },

  // Empty state
  empty: { alignItems: "center", paddingVertical: 60, gap: 10 },
  emptyIcon: { fontSize: 48 },
  emptyTitle: {
    fontFamily: FONTS.displayBold, fontSize: 22, textTransform: "uppercase",
    color: COLORS.text,
  },
  emptyDesc: {
    fontFamily: FONTS.body, fontSize: 14, color: COLORS.textSecondary,
    textAlign: "center", lineHeight: 20,
  },
  emptyBtn: {
    marginTop: 14, minHeight: 48, paddingHorizontal: 24, justifyContent: "center",
    backgroundColor: COLORS.accent, borderRadius: 14,
  },
  emptyBtnText: {
    fontFamily: FONTS.displayBold, fontSize: 17, letterSpacing: 0.6,
    textTransform: "uppercase", color: COLORS.onAccent,
  },
});
