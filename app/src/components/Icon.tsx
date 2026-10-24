/**
 * Icon — pictogrammes SVG (remplace les emojis).
 * Tous en viewBox 24, trait arrondi, couleur et épaisseur paramétrables.
 */
import React from "react";
import Svg, { Path, Rect, Circle, Polygon } from "react-native-svg";

export type IconName =
  | "search" | "calendar" | "star" | "tv" | "bell"
  | "check" | "close" | "plus" | "refresh";

interface Props {
  name: IconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
  /** Remplit la forme (étoile, cloche) au lieu de la tracer seulement. */
  filled?: boolean;
}

export function Icon({
  name, size = 22, color = "#F2F5FF", strokeWidth = 2.2, filled = false,
}: Props) {
  const stroke = {
    stroke: color,
    strokeWidth,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  const fill = filled ? color : "none";

  let body: React.ReactNode;
  switch (name) {
    case "search":
      body = (
        <>
          <Circle cx={11} cy={11} r={7} fill="none" {...stroke} />
          <Path d="M20 20l-4-4" fill="none" {...stroke} />
        </>
      );
      break;
    case "calendar":
      body = (
        <>
          <Rect x={3} y={4} width={18} height={17} rx={3} fill="none" {...stroke} />
          <Path d="M3 10h18M8 2v4M16 2v4" fill="none" {...stroke} />
        </>
      );
      break;
    case "star":
      body = (
        <Path
          d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"
          fill={fill}
          {...stroke}
        />
      );
      break;
    case "tv":
      body = (
        <>
          <Rect x={3} y={6} width={18} height={12} rx={2} fill="none" {...stroke} />
          <Path d="M9 21h6M12 18v3" fill="none" {...stroke} />
        </>
      );
      break;
    case "bell":
      body = (
        <>
          <Path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9" fill={fill} {...stroke} />
          <Path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" fill="none" {...stroke} />
        </>
      );
      break;
    case "check":
      body = <Path d="M5 12.5l4.5 4.5L19 7" fill="none" {...stroke} />;
      break;
    case "close":
      body = <Path d="M6 6l12 12M18 6L6 18" fill="none" {...stroke} />;
      break;
    case "plus":
      body = <Path d="M12 5v14M5 12h14" fill="none" {...stroke} />;
      break;
    case "refresh":
      body = (
        <>
          <Path d="M20 11a8 8 0 1 0-2.3 5.7" fill="none" {...stroke} />
          <Path d="M20 4v7h-7" fill="none" {...stroke} />
        </>
      );
      break;
  }

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      {body}
    </Svg>
  );
}

/** L'éclair de la marque (rempli). */
export function BoltMark({ size = 24, color = "#0A0E1A" }: { size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      <Polygon points="29,2 8,27 22,27 16,46 40,18 26,18" fill={color} />
    </Svg>
  );
}
