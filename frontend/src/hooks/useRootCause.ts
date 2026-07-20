import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface BreakdownItem {
  dimension: string;
  segment: string;
  delta: number;
  contributionPct: number;
}

export interface RootCauseData {
  id: string;
  tenantId: string;
  anomalyId: string;
  kpiName: string;
  periodCurrent: string;
  periodPrevious: string;
  deltaTotal: number;
  deltaTotalPct: number;
  breakdown: BreakdownItem[];
  residualPct: number;
  explanation: string;
  createdAt: string;
}

export function useRootCause(anomalyId: string | null | undefined) {
  return useQuery<RootCauseData>({
    queryKey: ["rootCause", anomalyId],
    queryFn: async () => {
      if (!anomalyId) throw new Error("anomalyId is required");
      const res = await api.get(`/api/anomalies/${anomalyId}/root-cause`);
      const data = res.data;
      return {
        id: data.id,
        tenantId: data.tenant_id,
        anomalyId: data.anomaly_id,
        kpiName: data.kpi_name,
        periodCurrent: data.period_current,
        periodPrevious: data.period_previous,
        deltaTotal: data.delta_total,
        deltaTotalPct: data.delta_total_pct,
        breakdown: (data.breakdown || []).map((b: any) => ({
          dimension: b.dimension,
          segment: b.segment,
          delta: b.delta,
          contributionPct: b.contribution_pct ?? b.contributionPct ?? 0,
        })),
        residualPct: data.residual_pct ?? 0,
        explanation: data.explanation || "",
        createdAt: data.created_at,
      };
    },
    enabled: !!anomalyId,
    staleTime: 5 * 60 * 1000,
  });
}
