/**
 * SportZap — useChannels hook
 *
 * Manages "Mes Chaînes" selection:
 *  - Persists to AsyncStorage
 *  - Provides toggle/selectAll/selectGroup helpers
 *  - Exposes active slugs as a Set for fast filtering
 *
 * Default: all free TNT channels selected on first launch.
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  ALL_CHANNELS,
  ChannelGroup,
  getDefaultChannelSlugs,
  getAllChannelSlugs,
  getChannelsByGroup,
} from "../constants/channels";

const STORAGE_KEY = "@sportzap_channels_v2";

// Plusieurs écrans (Programme, Chaînes) utilisent ce hook : chaque instance a son
// propre état, on les synchronise donc via un petit bus module-level.
const listeners = new Set<(slugs: Set<string>) => void>();
function broadcast(slugs: Set<string>) {
  listeners.forEach(l => l(slugs));
}

export function useChannels() {
  const [selectedSlugs, setSelectedSlugs] = useState<Set<string>>(getAllChannelSlugs());
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    listeners.add(setSelectedSlugs);
    return () => { listeners.delete(setSelectedSlugs); };
  }, []);

  // ── Load from storage on mount ──
  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem(STORAGE_KEY);
        if (stored) {
          const slugs: string[] = JSON.parse(stored);
          setSelectedSlugs(new Set(slugs));
        }
      } catch (e) {
        console.warn("Failed to load channel prefs:", e);
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  // ── Persist on change ──
  const persist = useCallback(async (slugs: Set<string>) => {
    // Hors phase de rendu (persist est appelé depuis un updater setState)
    Promise.resolve().then(() => broadcast(slugs));
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify([...slugs]));
    } catch (e) {
      console.warn("Failed to save channel prefs:", e);
    }
  }, []);

  // ── Toggle single channel ──
  const toggle = useCallback((slug: string) => {
    setSelectedSlugs(prev => {
      const next = new Set(prev);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      persist(next);
      return next;
    });
  }, [persist]);

  // ── Toggle entire group ──
  const toggleGroup = useCallback((group: ChannelGroup) => {
    setSelectedSlugs(prev => {
      const next = new Set(prev);
      const groupChannels = getChannelsByGroup(group);
      const allSelected = groupChannels.every(ch => next.has(ch.slug));

      if (allSelected) {
        // Deselect all in group
        groupChannels.forEach(ch => next.delete(ch.slug));
      } else {
        // Select all in group
        groupChannels.forEach(ch => next.add(ch.slug));
      }

      persist(next);
      return next;
    });
  }, [persist]);

  // ── Select all ──
  const selectAll = useCallback(() => {
    const all = getAllChannelSlugs();
    setSelectedSlugs(all);
    persist(all);
  }, [persist]);

  // ── Select free only (reset) ──
  const selectFreeOnly = useCallback(() => {
    const free = getDefaultChannelSlugs();
    setSelectedSlugs(free);
    persist(free);
  }, [persist]);

  // ── Check if group is fully/partially selected ──
  const isGroupSelected = useCallback((group: ChannelGroup): "all" | "some" | "none" => {
    const groupChannels = getChannelsByGroup(group);
    const selected = groupChannels.filter(ch => selectedSlugs.has(ch.slug));
    if (selected.length === groupChannels.length) return "all";
    if (selected.length > 0) return "some";
    return "none";
  }, [selectedSlugs]);

  // ── Stats ──
  const stats = useMemo(() => {
    const total = ALL_CHANNELS.length;
    const selected = selectedSlugs.size;
    const freeSelected = ALL_CHANNELS.filter(
      ch => ch.isFree && selectedSlugs.has(ch.slug)
    ).length;
    const paidSelected = selected - freeSelected;
    return { total, selected, freeSelected, paidSelected };
  }, [selectedSlugs]);

  return {
    selectedSlugs,
    loaded,
    toggle,
    toggleGroup,
    selectAll,
    selectFreeOnly,
    isGroupSelected,
    isSelected: (slug: string) => selectedSlugs.has(slug),
    stats,
  };
}
