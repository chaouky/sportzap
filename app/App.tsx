/**
 * SportZap — App Entry Point (direction « Night Match »)
 *
 * Sets up:
 *   - ThemeProvider (thème sombre)
 *   - Chargement des polices Barlow / Barlow Condensed
 *   - Navigation par onglets avec barre flottante
 */
import { registerRootComponent } from "expo";
import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { NavigationContainer, DarkTheme } from "@react-navigation/native";
import { createBottomTabNavigator, BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useFonts } from "expo-font";
import { StatusBar } from "expo-status-bar";

import { ThemeProvider } from "./src/hooks/useTheme";
import { HomeScreen } from "./src/screens/HomeScreen";
import { FavoritesScreen } from "./src/screens/FavoritesScreen";
import { ChannelsScreen } from "./src/screens/ChannelsScreen";
import { Icon, IconName, BoltMark } from "./src/components/Icon";
import { COLORS, FONTS } from "./src/constants";

const Tab = createBottomTabNavigator();

const TAB_ICONS: Record<string, IconName> = {
  Programme: "calendar",
  Favoris: "star",
  Chaînes: "tv",
};

function TabBar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.tabBar, { bottom: Math.max(insets.bottom, 8) + 8 }]}>
      {state.routes.map((route, index) => {
        const focused = state.index === index;
        const color = focused ? COLORS.onAccent : COLORS.textSecondary;

        const onPress = () => {
          const event = navigation.emit({
            type: "tabPress",
            target: route.key,
            canPreventDefault: true,
          });
          if (!focused && !event.defaultPrevented) {
            navigation.navigate(route.name as never);
          }
        };

        return (
          <TouchableOpacity
            key={route.key}
            style={[styles.tab, focused && styles.tabActive]}
            onPress={onPress}
            accessibilityRole="button"
            accessibilityState={{ selected: focused }}
            accessibilityLabel={route.name}
            activeOpacity={0.8}
          >
            <Icon name={TAB_ICONS[route.name] ?? "calendar"} size={22} color={color} />
            <Text style={[styles.tabLabel, { color }]}>{route.name}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

function AppContent() {
  const navTheme = {
    ...DarkTheme,
    colors: {
      ...DarkTheme.colors,
      background: COLORS.bg,
      card: COLORS.card,
      text: COLORS.text,
      border: COLORS.border,
      primary: COLORS.accent,
    },
  };

  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style="light" />
      <Tab.Navigator
        tabBar={props => <TabBar {...props} />}
        screenOptions={{ headerShown: false }}
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
    BarlowCondensedSemiBold: require("./assets/fonts/BarlowCondensed-SemiBold.ttf"),
    BarlowCondensedBold: require("./assets/fonts/BarlowCondensed-Bold.ttf"),
    BarlowCondensedExtraBold: require("./assets/fonts/BarlowCondensed-ExtraBold.ttf"),
    Barlow: require("./assets/fonts/Barlow-Regular.ttf"),
    BarlowMedium: require("./assets/fonts/Barlow-Medium.ttf"),
    BarlowSemiBold: require("./assets/fonts/Barlow-SemiBold.ttf"),
  });

  if (!fontsLoaded) {
    return (
      <View style={styles.loading}>
        <BoltMark size={64} color={COLORS.accent} />
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
    backgroundColor: COLORS.bg,
  },
  tabBar: {
    position: "absolute",
    left: 12, right: 12,
    height: 68,
    flexDirection: "row",
    padding: 6, gap: 4,
    backgroundColor: COLORS.card,
    borderWidth: 1, borderColor: COLORS.border,
    borderRadius: 24,
  },
  tab: {
    flex: 1,
    borderRadius: 18,
    alignItems: "center", justifyContent: "center",
    gap: 3,
  },
  tabActive: { backgroundColor: COLORS.accent },
  tabLabel: { fontFamily: FONTS.bodySemi, fontSize: 12 },
});

registerRootComponent(App);
