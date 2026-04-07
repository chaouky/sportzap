/**
 * EntityAvatar — Renders the appropriate visual for an entity:
 *   club    → rounded square with ESPN logo or monogram
 *   country → flag from flagcdn.com
 *   player  → circular photo with mini flag badge
 */
import React, { useState } from "react";
import { View, Image, Text, StyleSheet } from "react-native";
import { Entity } from "../types";
import { flagUrl } from "../constants";

interface Props {
  entity: Entity | null | undefined;
  size?: number;
  side?: "left" | "right";
}

export function EntityAvatar({ entity, size = 36, side = "left" }: Props) {
  const [imgError, setImgError] = useState(false);

  if (!entity) return null;

  const borderRadius = entity.type === "player" ? size / 2 : size * 0.25;

  // ── Fallback monogram ──
  const Monogram = ({ color = "rgba(0,0,0,0.3)" }: { color?: string }) => (
    <View style={[styles.container, {
      width: size, height: size, borderRadius,
      backgroundColor: "rgba(0,0,0,0.04)",
    }]}>
      <Text style={[styles.monogram, {
        fontSize: size * 0.3, color,
      }]}>
        {entity.name.slice(0, 2).toUpperCase()}
      </Text>
    </View>
  );

  // ── CLUB ──
  if (entity.type === "club") {
    if (entity.logo_url && !imgError) {
      return (
        <View style={[styles.container, {
          width: size, height: size, borderRadius,
          backgroundColor: "rgba(0,0,0,0.02)",
          borderWidth: 1,
          borderColor: "rgba(0,0,0,0.06)",
        }]}>
          <Image
            source={{ uri: entity.logo_url }}
            style={{ width: size * 0.72, height: size * 0.72 }}
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
    return (
      <View style={[styles.container, {
        width: size, height: size, borderRadius,
        overflow: "hidden",
        borderWidth: 1,
        borderColor: "rgba(0,0,0,0.06)",
        backgroundColor: "#f0f0f0",
      }]}>
        {!imgError ? (
          <Image
            source={{ uri: flagUrl(entity.country_code) }}
            style={{ width: size * 1.1, height: size * 1.1 }}
            resizeMode="cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <Text style={[styles.monogram, { fontSize: size * 0.3 }]}>
            {entity.country_code.toUpperCase()}
          </Text>
        )}
      </View>
    );
  }

  // ── PLAYER ──
  if (entity.type === "player") {
    return (
      <View style={{ position: "relative" }}>
        <View style={[styles.container, {
          width: size, height: size, borderRadius: size / 2,
          overflow: "hidden",
          borderWidth: 2,
          borderColor: "rgba(0,0,0,0.08)",
          backgroundColor: "rgba(0,0,0,0.04)",
        }]}>
          {entity.photo_url && !imgError ? (
            <Image
              source={{ uri: entity.photo_url }}
              style={{ width: size, height: size }}
              resizeMode="cover"
              onError={() => setImgError(true)}
            />
          ) : (
            <Text style={[styles.monogram, {
              fontSize: size * 0.32,
              color: "rgba(0,0,0,0.4)",
            }]}>
              {entity.name.charAt(0)}
            </Text>
          )}
        </View>

        {/* Mini flag badge */}
        {entity.country_code && (
          <View style={[styles.flagBadge, {
            [side === "left" ? "right" : "left"]: -3,
            width: 16, height: 16,
          }]}>
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

  // ── EVENT / FALLBACK ──
  return <Monogram />;
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
  },
  monogram: {
    fontFamily: "DMMono",
    fontWeight: "700",
    letterSpacing: -0.5,
  },
  flagBadge: {
    position: "absolute",
    bottom: -2,
    borderRadius: 8,
    overflow: "hidden",
    borderWidth: 2,
    borderColor: "#F5F2ED",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#eee",
  },
});
