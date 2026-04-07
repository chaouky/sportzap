/**
 * SportZap — useFavorites hook
 *
 * Manages followed teams, competitions, and sports.
 * Persists to AsyncStorage.
 * Exposes matching logic for highlighting events.
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  COMPETITIONS,
  POPULAR_TEAMS,
  Followable,
  matchEventToFavorites,
} from "../constants/favorites";

const STORAGE_KEY = "@sportzap_favorites";

export function useFavorites() {
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());
  const [loaded, setLoaded] = useState(false);

  // ── Load ──
  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem(STORAGE_KEY);
        if (stored) {
          setFavoriteIds(new Set(JSON.parse(stored)));
        }
      } catch (e) {
        console.warn("Failed to load favorites:", e);
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  // ── Persist ──
  const persist = useCallback(async (ids: Set<string>) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
    } catch (e) {
      console.warn("Failed to save favorites:", e);
    }
  }, []);

  // ── Toggle ──
  const toggle = useCallback((id: string) => {
    setFavoriteIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      persist(next);
      return next;
    });
  }, [persist]);

  // ── Clear all ──
  const clearAll = useCallback(() => {
    setFavoriteIds(new Set());
    persist(new Set());
  }, [persist]);

  // ── Query helpers ──
  const isFollowing = useCallback((id: string) => favoriteIds.has(id), [favoriteIds]);

  const followedTeams = useMemo(() =>
    POPULAR_TEAMS.filter(t => favoriteIds.has(t.id)),
    [favoriteIds]
  );

  const followedCompetitions = useMemo(() =>
    COMPETITIONS.filter(c => favoriteIds.has(c.id)),
    [favoriteIds]
  );

  /**
   * Check if a sport event matches any favorite.
   * Returns matching favorite IDs (empty array = not relevant).
   */
  const matchEvent = useCallback((event: {
    team1?: { name: string } | null;
    team2?: { name: string } | null;
    competition?: string | null;
    sport: string;
  }) => {
    if (favoriteIds.size === 0) return [];
    return matchEventToFavorites(event, favoriteIds);
  }, [favoriteIds]);

  const stats = useMemo(() => ({
    totalFollowed: favoriteIds.size,
    teams: followedTeams.length,
    competitions: followedCompetitions.length,
  }), [favoriteIds, followedTeams, followedCompetitions]);

  return {
    favoriteIds,
    loaded,
    toggle,
    clearAll,
    isFollowing,
    followedTeams,
    followedCompetitions,
    matchEvent,
    stats,
  };
}
