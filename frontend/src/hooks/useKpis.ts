import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { KPI } from "@/types";

async function fetchKpis(): Promise<KPI[]> {
  const { data } = await api.get("/api/kpis");
  return data;
}

export function useKpis() {
  return useQuery({
    queryKey: ["kpis"],
    queryFn: fetchKpis,
  });
}