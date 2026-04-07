/**
 * SportIcon — SVG sport pictograms
 *
 * Uses simple path-based icons to avoid emoji inconsistency.
 * Falls back to a generic circle for unknown sports.
 *
 * Note: In production, use react-native-svg.
 * For now, we use Text-based fallback that works without native deps.
 */
import React from "react";
import { Text } from "react-native";
import { SportType } from "../types";

// Emoji fallback map (works everywhere without native SVG)
const SPORT_EMOJI: Record<string, string> = {
  football: "⚽",
  rugby: "🏉",
  tennis: "🎾",
  basket: "🏀",
  f1: "🏎",
  cyclisme: "🚴",
  mma: "🥊",
  handball: "🤾",
  boxe: "🥊",
  natation: "🏊",
  athletisme: "🏃",
  ski: "⛷",
  golf: "⛳",
  voile: "⛵",
  motogp: "🏍",
  volleyball: "🏐",
  equitation: "🏇",
  other: "🏅",
};

interface Props {
  sport: SportType;
  color?: string;
  size?: number;
}

/**
 * Renders a sport icon.
 *
 * TODO: Replace emoji with react-native-svg paths
 * for pixel-perfect rendering matching the web prototype.
 */
export function SportIcon({ sport, color, size = 16 }: Props) {
  const emoji = SPORT_EMOJI[sport] || SPORT_EMOJI.other;

  return (
    <Text style={{ fontSize: size - 2, lineHeight: size + 2 }}>
      {emoji}
    </Text>
  );
}
