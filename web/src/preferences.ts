import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | null;

export interface LastLeague {
  code: string;
  season?: number;
}

interface PreferencesState {
  theme: Theme;
  lastLeague: LastLeague;
  setTheme: (theme: Theme) => void;
  setLastLeague: (lastLeague: LastLeague) => void;
}

export const usePreferences = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: null,
      lastLeague: { code: "E0" },
      setTheme: (theme) => set({ theme }),
      setLastLeague: (lastLeague) => set({ lastLeague }),
    }),
    { name: "scorecaster-preferences" },
  ),
);

export function applyTheme(theme: Theme): void {
  if (theme === null) {
    delete document.documentElement.dataset.theme;
  } else {
    document.documentElement.dataset.theme = theme;
  }
}
