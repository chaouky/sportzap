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
import { COLORS } from "../constants";
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
          trackColor={{ false: "rgba(0,0,0,0.08)", true: `${COLORS.accent}40` }}
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
              trackColor={{ false: "rgba(0,0,0,0.08)", true: `${COLORS.accent}40` }}
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
              trackColor={{ false: "rgba(0,0,0,0.08)", true: `${COLORS.accent}40` }}
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
  container: { paddingHorizontal: 22, paddingTop: 20 },
  sectionTitle: {
    fontSize: 11, fontWeight: "500", letterSpacing: 2,
    color: "rgba(0,0,0,0.28)", fontFamily: "DMMono",
    marginBottom: 16,
  },

  row: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: "rgba(0,0,0,0.04)",
  },
  rowTitle: {
    fontSize: 15, fontWeight: "500", color: COLORS.text,
  },
  rowDesc: {
    fontSize: 12, color: COLORS.textSecondary,
    fontFamily: "DMMono", marginTop: 2, lineHeight: 16,
  },

  timingRow: {
    flexDirection: "row", gap: 6,
    paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: "rgba(0,0,0,0.04)",
  },
  timingBtn: {
    flex: 1, paddingVertical: 10, borderRadius: 10,
    backgroundColor: "rgba(0,0,0,0.03)",
    alignItems: "center",
  },
  timingBtnActive: {
    backgroundColor: COLORS.text,
  },
  timingText: {
    fontSize: 12, fontWeight: "600",
    fontFamily: "DMMono",
    color: "rgba(0,0,0,0.3)",
  },
  timingTextActive: { color: COLORS.bg },

  clearBtn: {
    marginTop: 20, paddingVertical: 14,
    borderRadius: 14,
    borderWidth: 1.5, borderColor: "rgba(239,68,68,0.15)",
    backgroundColor: "rgba(239,68,68,0.03)",
    alignItems: "center",
  },
  clearBtnText: {
    fontSize: 13, fontWeight: "600",
    color: "#EF4444", fontFamily: "DMMono",
  },
});
