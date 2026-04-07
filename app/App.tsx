/**
 * SportZap — App Entry Point
 *
 * Sets up:
 *   - ThemeProvider (light/dark)
 *   - Custom font loading
 *   - Bottom tab navigation with theme-aware styling
 */
import { registerRootComponent } from "expo";
import React from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { NavigationContainer, DefaultTheme, DarkTheme } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { useFonts } from "expo-font";
import { StatusBar } from "expo-status-bar";

import { ThemeProvider, useTheme } from "./src/hooks/useTheme";
import { HomeScreen } from "./src/screens/HomeScreen";
import { FavoritesScreen } from "./src/screens/FavoritesScreen";
import { ChannelsScreen } from "./src/screens/ChannelsScreen";

const Tab = createBottomTabNavigator();

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  const icons: Record<string, string> = {
    Programme: "📺",
    Favoris: "⭐",
    Chaînes: "📡",
  };
  return (
    <Text style={{ fontSize: 20, opacity: focused ? 1 : 0.3 }}>
      {icons[label] || "📱"}
    </Text>
  );
}

function AppContent() {
  const { theme, isDark } = useTheme();
  const c = theme.colors;

  const navTheme = {
    ...(isDark ? DarkTheme : DefaultTheme),
    colors: {
      ...(isDark ? DarkTheme : DefaultTheme).colors,
      background: c.bg,
      card: c.navBg,
      text: c.text,
      border: c.navBorder,
      primary: c.accent,
    },
  };

  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style={isDark ? "light" : "dark"} />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarIcon: ({ focused }) => <TabIcon label={route.name} focused={focused} />,
          tabBarActiveTintColor: c.navActive,
          tabBarInactiveTintColor: c.navInactive,
          tabBarLabelStyle: {
            fontSize: 10,
            fontFamily: "DMMono",
            letterSpacing: 0.5,
          },
          tabBarStyle: {
            backgroundColor: c.navBg,
            borderTopWidth: 0,
            elevation: 0,
            shadowColor: "#000",
            shadowOpacity: isDark ? 0.3 : 0.04,
            shadowRadius: 20,
            shadowOffset: { width: 0, height: -4 },
            height: 85,
            paddingTop: 8,
            paddingBottom: 28,
            borderRadius: 22,
            marginHorizontal: 16,
            marginBottom: 16,
            position: "absolute",
            borderWidth: isDark ? 1 : 0,
            borderColor: c.navBorder,
          },
        })}
      >
        <Tab.Screen name="Programme" component={HomeScreen} />
        <Tab.Screen name="Favoris" component={FavoritesScreen} />
        <Tab.Screen name="Chaînes" component={ChannelsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  const [fontsLoaded] = useFonts({
    InstrumentSerif: require("./assets/fonts/InstrumentSerif-Regular.ttf"),
    InstrumentSerifItalic: require("./assets/fonts/InstrumentSerif-Italic.ttf"),
    DMMono: require("./assets/fonts/DMMono-Regular.ttf"),
    DMMonoMedium: require("./assets/fonts/DMMono-Medium.ttf"),
  });

  if (!fontsLoaded) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#6366F1" />
      </View>
    );
  }

  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1, alignItems: "center", justifyContent: "center",
    backgroundColor: "#F5F2ED",
  },
});

registerRootComponent(App);
