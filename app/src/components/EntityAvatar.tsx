/**
 * EntityAvatar — visuel d'une équipe / pays / joueur, en rond.
 *   club    → logo sur pastille claire (les logos ESPN sont conçus pour fond clair)
 *   country → drapeau
 *   player  → photo + mini drapeau
 *   défaut  → monogramme sur fond sombre
 */
import React, { useState } from "react";
import { View, Image, Text, StyleSheet } from "react-native";
import { Entity } from "../types";
import { COLORS, FONTS, flagUrl } from "../constants";

interface Props {
  entity: Entity | null | undefined;
  size?: number;
  side?: "left" | "right";
}

export function EntityAvatar({ entity, size = 36, side = "left" }: Props) {
  const [imgError, setImgError] = useState(false);

  if (!entity) return null;

  const base = { width: size, height: size, borderRadius: size / 2 };
  const initials = entity.name.slice(0, 3).toUpperCase();

  const Monogram = () => (
    <View style={[styles.center, base, styles.mono]}>
      <Text style={[styles.monoText, { fontSize: size * 0.34 }]}>{initials}</Text>
    </View>
  );

  // ── CLUB ──
  if (entity.type === "club") {
    if (entity.logo_url && !imgError) {
      return (
        <View style={[styles.center, base, styles.logoBg]}>
          <Image
            source={{ uri: entity.logo_url }}
            style={{ width: size * 0.66, height: size * 0.66 }}
            resizeMode="contain"
            onError={() => setImgError(true)}
          />
        </View>
      );
    }
    return <Monogram />;
  }

  // ── COUNTRY ──
  if (entity.type === "country" && entity.country_code) {
    if (imgError) return <Monogram />;
    return (
      <View style={[styles.center, base, styles.flagWrap]}>
        <Image
          source={{ uri: flagUrl(entity.country_code) }}
          style={{ width: size * 1.1, height: size * 1.1 }}
          resizeMode="cover"
          onError={() => setImgError(true)}
        />
      </View>
    );
  }

  // ── PLAYER ──
  if (entity.type === "player") {
    return (
      <View style={{ position: "relative" }}>
        <View style={[styles.center, base, styles.photoWrap]}>
          {entity.photo_url && !imgError ? (
            <Image
              source={{ uri: entity.photo_url }}
              style={{ width: size, height: size }}
              resizeMode="cover"
              onError={() => setImgError(true)}
            />
          ) : (
            <Text style={[styles.monoText, { fontSize: size * 0.4 }]}>
              {entity.name.charAt(0)}
            </Text>
          )}
        </View>
        {entity.country_code && (
          <View
            style={[
              styles.flagBadge,
              { [side === "left" ? "right" : "left"]: -3, width: 16, height: 16 },
            ]}
          >
            <Image
              source={{ uri: flagUrl(entity.country_code, 40) }}
              style={{ width: 20, height: 20 }}
              resizeMode="cover"
            />
          </View>
        )}
      </View>
    );
  }

  return <Monogram />;
}

const styles = StyleSheet.create({
  center: { alignItems: "center", justifyContent: "center" },
  mono: {
    backgroundColor: COLORS.surface2,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  monoText: {
    fontFamily: FONTS.displayBold,
    color: COLORS.text,
    letterSpacing: 0.2,
  },
  logoBg: { backgroundColor: COLORS.text },
  flagWrap: {
    overflow: "hidden",
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface2,
  },
  photoWrap: {
    overflow: "hidden",
    borderWidth: 2,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface2,
  },
  flagBadge: {
    position: "absolute",
    bottom: -2,
    borderRadius: 8,
    overflow: "hidden",
    borderWidth: 2,
    borderColor: COLORS.card,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: COLORS.surface2,
  },
});
