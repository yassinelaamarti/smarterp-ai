import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Alert {
  id: string;
  kpiId: string;
  severity: "warning" | "critical";
  message: string;
}

interface AlertApiResponse {
  id: string;
  kpi_id: string;
  severity: "warning" | "critical";
  message: string;
}

async function fetchAlerts(): Promise<Alert[]> {
  const { data } = await api.get<AlertApiResponse[]>("/api/alerts/");
  return data.map((a) => ({
    id: a.id,
    kpiId: a.kpi_id,
    severity: a.severity,
    message: a.message,
  }));
}

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 60_000,
  });
}
