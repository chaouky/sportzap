/**
 * Logo — pastille lime + éclair, et mot-symbole SPORTZAP.
 */
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { COLORS, FONTS } from "../constants";
import { BoltMark } from "./Icon";

export function Logo({ size = 36 }: { size?: number }) {
  return (
    <View style={styles.row}>
      <View
        style={[
          styles.mark,
          { width: size, height: size, borderRadius: size * 0.28 },
        ]}
      >
        <BoltMark size={size * 0.6} color={COLORS.onAccent} />
      </View>
      <Text style={[styles.word, { fontSize: size * 0.78, lineHeight: size * 0.9 }]}>
        SPORT<Text style={styles.zap}>ZAP</Text>
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 10 },
  mark: {
    backgroundColor: COLORS.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  word: {
    fontFamily: FONTS.display,
    color: COLORS.text,
    letterSpacing: 0.6,
  },
  zap: { color: COLORS.accent },
});
