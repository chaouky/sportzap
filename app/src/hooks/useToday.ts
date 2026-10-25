/**
 * SportZap — useToday
 *
 * Date du jour à Paris (YYYY-MM-DD), mise à jour quand l'app reste ouverte
 * au-delà de minuit ou revient au premier plan. Évite les onglets « jours »
 * figés sur la date du lancement.
 */
import { useEffect, useState } from "react";
import { AppState } from "react-native";
import { todayParisISO } from "../constants";

export function useToday(): string {
  const [today, setToday] = useState(todayParisISO());

  useEffect(() => {
    const check = () => setToday(prev => {
      const now = todayParisISO();
      return now === prev ? prev : now;
    });
    const timer = setInterval(check, 60 * 1000);
    const sub = AppState.addEventListener("change", state => {
      if (state === "active") check();
    });
    return () => { clearInterval(timer); sub.remove(); };
  }, []);

  return today;
}
