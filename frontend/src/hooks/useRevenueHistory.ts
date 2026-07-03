import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface RevenuePoint {
  month: string;
  label: string;
  revenue: number;
}

async function fetchRevenueHistory(months: number): Promise<RevenuePoint[]> {
  const { data } = await api.get<RevenuePoint[]>("/api/kpis/revenue-history", {
    params: { months },
  });
  return data;
}

export function useRevenueHistory(months: number = 6) {
  return useQuery({
    queryKey: ["revenue-history", months],
    queryFn: () => fetchRevenueHistory(months),
    refetchInterval: 60_000,
  });
}
