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
  StyleSheet, SafeAreaView, Image,
} from "react-native";
import { COLORS } from "../constants";
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
          <View style={[styles.itemAvatar, { backgroundColor: `${item.badgeBg}10`, borderColor: `${item.badgeBg}20` }]}>
            <Image source={{ uri: item.logoUrl }} style={{ width: 24, height: 24 }} resizeMode="contain" />
          </View>
        ) : item.flagCode ? (
          <View style={[styles.itemAvatar, { borderColor: "rgba(0,0,0,0.06)", overflow: "hidden" }]}>
            <Image source={{ uri: `https://flagcdn.com/w80/${item.flagCode}.png` }} style={{ width: 38, height: 38 }} resizeMode="cover" />
          </View>
        ) : (
          <View style={[styles.itemAvatar, { backgroundColor: `${item.badgeBg}15` }]}>
            <Text style={[styles.itemAvatarText, { color: item.badgeBg }]}>{item.short.slice(0, 3)}</Text>
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
    <SafeAreaView style={styles.safe}>
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
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            style={styles.searchInput}
            placeholder="Rechercher une équipe, une compétition..."
            placeholderTextColor="rgba(0,0,0,0.25)"
            value={search}
            onChangeText={setSearch}
            onFocus={() => setActiveTab("discover")}
          />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => setSearch("")}>
              <Text style={styles.searchClear}>✕</Text>
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
                <Text style={styles.emptyIcon}>⭐</Text>
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
                <Text style={styles.emptyIcon}>🔍</Text>
                <Text style={styles.emptyTitle}>Aucun résultat</Text>
                <Text style={styles.emptyDesc}>
                  Essayez un autre terme de recherche
                </Text>
              </View>
            ) : (
              groupedDiscover.map(group => (
                <View key={group.sport} style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Text style={styles.sectionIcon}>{group.icon}</Text>
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
  scrollContent: { paddingBottom: 120 },

  header: { paddingHorizontal: 22, paddingTop: 8 },
  title: {
    fontSize: 36, fontWeight: "400",
    fontFamily: "InstrumentSerif",
    color: COLORS.text, letterSpacing: -1,
  },
  titleAccent: { fontStyle: "italic", color: COLORS.accent },
  subtitle: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono", letterSpacing: 1.5, marginTop: 4,
  },

  // Search
  searchContainer: {
    flexDirection: "row", alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 14, borderWidth: 1,
    borderColor: "rgba(0,0,0,0.06)",
    marginHorizontal: 22, marginTop: 20,
    paddingHorizontal: 14, height: 46,
  },
  searchIcon: { fontSize: 14, marginRight: 10, opacity: 0.3 },
  searchInput: {
    flex: 1, fontSize: 14, color: COLORS.text,
    fontFamily: "DMMono",
  },
  searchClear: {
    fontSize: 16, color: "rgba(0,0,0,0.25)",
    padding: 4,
  },

  // Tabs
  tabs: {
    flexDirection: "row", marginHorizontal: 22,
    marginTop: 20, borderBottomWidth: 1.5,
    borderBottomColor: "rgba(0,0,0,0.06)",
  },
  tab: {
    paddingBottom: 12, marginRight: 24,
    borderBottomWidth: 2.5, borderBottomColor: "transparent",
    marginBottom: -1.5,
  },
  tabActive: { borderBottomColor: COLORS.text },
  tabText: {
    fontSize: 13, fontWeight: "500",
    color: "rgba(0,0,0,0.25)", fontFamily: "DMMono",
  },
  tabTextActive: { color: COLORS.text },

  // Content
  content: { paddingHorizontal: 22, paddingTop: 20 },

  // Sections
  section: { marginBottom: 24 },
  sectionHeader: {
    flexDirection: "row", alignItems: "center",
    gap: 8, marginBottom: 12,
  },
  sectionIcon: { fontSize: 14 },
  sectionLabel: {
    fontSize: 11, fontWeight: "500", letterSpacing: 2,
    color: "rgba(0,0,0,0.28)", fontFamily: "DMMono",
  },
  sectionLine: {
    flex: 1, height: 1, backgroundColor: "rgba(0,0,0,0.04)",
  },

  // Card container
  card: {
    backgroundColor: "#fff", borderRadius: 16,
    borderWidth: 1, borderColor: "rgba(0,0,0,0.04)",
    overflow: "hidden",
  },

  // Item rows
  itemRow: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12, paddingHorizontal: 14,
    borderBottomWidth: 1, borderBottomColor: "rgba(0,0,0,0.03)",
  },
  itemRowFollowed: {},
  itemLeft: {
    flexDirection: "row", alignItems: "center", gap: 12, flex: 1,
  },
  itemAvatar: {
    width: 36, height: 36, borderRadius: 10,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(0,0,0,0.06)",
  },
  itemAvatarText: {
    fontSize: 11, fontWeight: "700", fontFamily: "DMMono",
  },
  itemName: {
    fontSize: 14, fontWeight: "500", color: COLORS.text,
  },
  itemMeta: {
    fontSize: 11, color: COLORS.textSecondary,
    fontFamily: "DMMono", marginTop: 1,
  },

  // Follow button
  followBtn: {
    paddingHorizontal: 14, paddingVertical: 7,
    borderRadius: 20, borderWidth: 1.5,
  },
  followBtnActive: {
    backgroundColor: `${COLORS.accent}10`,
    borderColor: `${COLORS.accent}30`,
  },
  followBtnInactive: {
    backgroundColor: "transparent",
    borderColor: "rgba(0,0,0,0.08)",
  },
  followBtnText: {
    fontSize: 12, fontWeight: "600", fontFamily: "DMMono",
  },
  followBtnTextActive: { color: COLORS.accent },
  followBtnTextInactive: { color: "rgba(0,0,0,0.3)" },

  // Empty state
  empty: {
    alignItems: "center", paddingVertical: 60,
  },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: {
    fontSize: 15, fontWeight: "600", color: "rgba(0,0,0,0.35)",
  },
  emptyDesc: {
    fontSize: 12, color: "rgba(0,0,0,0.2)",
    marginTop: 6, textAlign: "center", lineHeight: 18,
  },
  emptyBtn: {
    marginTop: 20, paddingHorizontal: 24, paddingVertical: 12,
    backgroundColor: COLORS.text, borderRadius: 24,
  },
  emptyBtnText: {
    fontSize: 13, fontWeight: "600", color: COLORS.bg,
    fontFamily: "DMMono",
  },
});
