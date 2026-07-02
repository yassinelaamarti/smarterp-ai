import { create } from "zustand";

interface DashboardState {
  selectedPeriod: "week" | "month" | "quarter";
  setSelectedPeriod: (period: "week" | "month" | "quarter") => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  selectedPeriod: "month",
  setSelectedPeriod: (period) => set({ selectedPeriod: period }),
}));