"use client";

import { useState } from "react";
import { useKpis } from "@/hooks/useKpis";
import { MetricCard } from "./MetricCard";
import { KPIDetailModal } from "./KPIDetailModal";
import type { KPI } from "@/types";

export function KPIGrid() {
  const { data: kpis, isLoading, isError, error } = useKpis();
  const [selectedKpi, setSelectedKpi] = useState<KPI | null>(null);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-slate-100"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Impossible de charger les KPIs : {(error as Error)?.message ?? "erreur inconnue"}.
        <br />
        Vérifie que le backend tourne bien sur {process.env.NEXT_PUBLIC_API_URL}.
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {kpis?.map((kpi) => (
          <MetricCard key={kpi.id} kpi={kpi} onClick={setSelectedKpi} />
        ))}
      </div>
      
      {selectedKpi && (
        <KPIDetailModal kpi={selectedKpi} onClose={() => setSelectedKpi(null)} />
      )}
    </>
  );
}

