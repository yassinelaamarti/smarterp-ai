import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface HealthScoreFactor {
  label: string;
  impact: number;
}

export interface HealthScore {
  score: number;
  label: string;
  factors: HealthScoreFactor[];
}

async function fetchHealthScore(): Promise<HealthScore> {
  const { data } = await api.get<HealthScore>("/api/health-score/");
  return data;
}

export function useHealthScore() {
  return useQuery({
    queryKey: ["health-score"],
    queryFn: fetchHealthScore,
    refetchInterval: 60_000,
  });
}
