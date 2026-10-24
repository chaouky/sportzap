/**
 * NotificationSettings — Inline settings panel
 *
 * Shown in a modal or settings screen.
 * Controls: enabled, minutes before, sound, auto-favorite alerts.
 */
import React, { useState, useEffect } from "react";
import {
  View, Text, TouchableOpacity, Switch,
  StyleSheet,
} from "react-native";
import { COLORS, FONTS } from "../constants";
import { loadPrefs, savePrefs, NotifPrefs, cancelAllAlerts } from "../services/notifications";

const TIMING_OPTIONS = [
  { value: 5, label: "5 min" },
  { value: 10, label: "10 min" },
  { value: 15, label: "15 min" },
  { value: 30, label: "30 min" },
  { value: 60, label: "1 heure" },
];

export function NotificationSettings() {
  const [prefs, setPrefs] = useState<NotifPrefs>({
    enabled: true,
    minutesBefore: 15,
    soundEnabled: true,
    favoriteAutoAlert: true,
  });

  useEffect(() => {
    loadPrefs().then(setPrefs);
  }, []);

  const update = (patch: Partial<NotifPrefs>) => {
    const next = { ...prefs, ...patch };
    setPrefs(next);
    savePrefs(next);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>NOTIFICATIONS</Text>

      {/* Master toggle */}
      <View style={styles.row}>
        <View style={{ flex: 1 }}>
          <Text style={styles.rowTitle}>Alertes match</Text>
          <Text style={styles.rowDesc}>Recevoir un rappel avant les matchs</Text>
        </View>
        <Switch
          value={prefs.enabled}
          onValueChange={(v) => update({ enabled: v })}
          trackColor={{ false: COLORS.border, true: `${COLORS.accent}40` }}
          thumbColor={prefs.enabled ? COLORS.accent : "#ccc"}
        />
      </View>

      {prefs.enabled && (
        <>
          {/* Timing */}
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.rowTitle}>Délai de rappel</Text>
              <Text style={styles.rowDesc}>Combien de temps avant le coup d'envoi</Text>
            </View>
          </View>
          <View style={styles.timingRow}>
            {TIMING_OPTIONS.map(opt => (
              <TouchableOpacity
                key={opt.value}
                style={[
                  styles.timingBtn,
                  prefs.minutesBefore === opt.value && styles.timingBtnActive,
                ]}
                onPress={() => update({ minutesBefore: opt.value })}
              >
                <Text style={[
                  styles.timingText,
                  prefs.minutesBefore === opt.value && styles.timingTextActive,
                ]}>
                  {opt.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Sound */}
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.rowTitle}>Son</Text>
              <Text style={styles.rowDesc}>Jouer un son avec la notification</Text>
            </View>
            <Switch
              value={prefs.soundEnabled}
              onValueChange={(v) => update({ soundEnabled: v })}
              trackColor={{ false: COLORS.border, true: `${COLORS.accent}40` }}
              thumbColor={prefs.soundEnabled ? COLORS.accent : "#ccc"}
            />
          </View>

          {/* Auto-favorite */}
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.rowTitle}>Alertes auto favoris</Text>
              <Text style={styles.rowDesc}>
                Programmer automatiquement un rappel pour{"\n"}les matchs de vos équipes et compétitions suivies
              </Text>
            </View>
            <Switch
              value={prefs.favoriteAutoAlert}
              onValueChange={(v) => update({ favoriteAutoAlert: v })}
              trackColor={{ false: COLORS.border, true: `${COLORS.accent}40` }}
              thumbColor={prefs.favoriteAutoAlert ? COLORS.accent : "#ccc"}
            />
          </View>

          {/* Clear all */}
          <TouchableOpacity
            style={styles.clearBtn}
            onPress={() => cancelAllAlerts()}
          >
            <Text style={styles.clearBtnText}>Supprimer toutes les alertes programmées</Text>
          </TouchableOpacity>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingHorizontal: 20, paddingTop: 20 },
  sectionTitle: {
    fontFamily: FONTS.displayBold, fontSize: 17, letterSpacing: 2.6,
    color: COLORS.textSecondary, marginBottom: 16,
  },

  row: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  rowTitle: { fontFamily: FONTS.bodySemi, fontSize: 16, color: COLORS.text },
  rowDesc: {
    fontFamily: FONTS.body, fontSize: 13, color: COLORS.textSecondary,
    marginTop: 2, lineHeight: 18,
  },

  timingRow: {
    flexDirection: "row", gap: 6, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  timingBtn: {
    flex: 1, minHeight: 44, borderRadius: 10,
    backgroundColor: COLORS.card, borderWidth: 1, borderColor: COLORS.border,
    alignItems: "center", justifyContent: "center",
  },
  timingBtnActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  timingText: { fontFamily: FONTS.bodySemi, fontSize: 13, color: COLORS.text },
  timingTextActive: { color: COLORS.onAccent },

  clearBtn: {
    marginTop: 20, minHeight: 48, borderRadius: 14,
    borderWidth: 1, borderColor: "rgba(255,107,107,0.4)",
    backgroundColor: "rgba(255,107,107,0.08)",
    alignItems: "center", justifyContent: "center",
  },
  clearBtnText: { fontFamily: FONTS.bodySemi, fontSize: 14, color: "#FF8A8A" },
});
