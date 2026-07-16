import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Alert {
  id: string;
  kpiId: string;
  severity: "warning" | "critical";
  message: string;
  isAnomaly: boolean;
}

interface AlertApiResponse {
  id: string;
  kpi_id: string;
  severity: "warning" | "critical";
  message: string;
  is_anomaly: boolean;
}

async function fetchAlerts(): Promise<Alert[]> {
  const { data } = await api.get<AlertApiResponse[]>("/api/alerts/");
  return data.map((a) => ({
    id: a.id,
    kpiId: a.kpi_id,
    severity: a.severity,
    message: a.message,
    isAnomaly: a.is_anomaly || false,
  }));
}

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 60_000,
  });
}
