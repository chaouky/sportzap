import React, { createContext, useContext } from "react";
import { COLORS, FONTS } from "../constants";

// Direction « Night Match » : thème sombre unique.
const theme = {
  colors: {
    // Surfaces
    bg: COLORS.bg,
    surface: COLORS.card,
    // Text
    text: COLORS.text,
    textSecondary: COLORS.textSecondary,
    // Borders
    border: COLORS.border,
    // Accent
    accent: COLORS.accent,
    // Navigation
    navBg: COLORS.card,
    navBorder: COLORS.border,
    navActive: COLORS.onAccent,
    navInactive: COLORS.textSecondary,
    // Misc
    white: "#FFFFFF",
  },
  fonts: FONTS,
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  radius: {
    sm: 6,
    md: 12,
    lg: 20,
  },
};

type Theme = typeof theme;

interface ThemeContextValue {
  theme: Theme;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme,
  isDark: true,
});

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => (
  <ThemeContext.Provider value={{ theme, isDark: true }}>
    {children}
  </ThemeContext.Provider>
);

export const useTheme = () => useContext(ThemeContext);
