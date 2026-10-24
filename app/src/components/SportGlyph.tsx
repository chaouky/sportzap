/**
 * SportGlyph — pictogramme de sport (SVG, trait arrondi comme Icon).
 * Les tracés sont dans constants/sportGlyphs.json.
 */
import React from "react";
import Svg, { Circle, Ellipse, G, Path } from "react-native-svg";
import glyphs from "../constants/sportGlyphs.json";

export type GlyphName = keyof typeof glyphs;

interface Props {
  name: GlyphName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

type Shape = (string | number)[];

export function SportGlyph({ name, size = 18, color = "#9AA6C4", strokeWidth = 2 }: Props) {
  const shapes = ((glyphs as Record<string, Shape[]>)[name] ?? glyphs.trophy) as Shape[];
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <G
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      >
        {shapes.map((s, i) => {
          switch (s[0]) {
            case "c":
              return <Circle key={i} cx={s[1] as number} cy={s[2] as number} r={s[3] as number} />;
            case "e":
              return (
                <Ellipse
                  key={i}
                  cx={s[1] as number} cy={s[2] as number}
                  rx={s[3] as number} ry={s[4] as number}
                  rotation={s[5] as number} origin={`${s[1]}, ${s[2]}`}
                />
              );
            case "f":
              return <Path key={i} d={s[1] as string} fill={color} stroke="none" />;
            default:
              return <Path key={i} d={s[1] as string} />;
          }
        })}
      </G>
    </Svg>
  );
}
