import React, { createContext, useContext } from "react";

const theme = {
  colors: {
    // Surfaces
    bg: "#FAF9F6",
    surface: "#F0EDE8",
    // Text
    text: "#1A1A1A",
    textSecondary: "#6B6560",
    // Borders
    border: "#E0DBD4",
    // Accent
    accent: "#C84B2F",
    // Navigation
    navBg: "#FFFFFF",
    navBorder: "#E0DBD4",
    navActive: "#C84B2F",
    navInactive: "#A09890",
    // Misc
    white: "#FFFFFF",
  },
  fonts: {
    serif: "InstrumentSerif",
    serifItalic: "InstrumentSerifItalic",
    mono: "DMMono",
    monoMedium: "DMMonoMedium",
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  radius: {
    sm: 4,
    md: 8,
    lg: 16,
  },
};

type Theme = typeof theme;

interface ThemeContextValue {
  theme: Theme;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme,
  isDark: false,
});

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => (
  <ThemeContext.Provider value={{ theme, isDark: false }}>
    {children}
  </ThemeContext.Provider>
);

export const useTheme = () => useContext(ThemeContext);
