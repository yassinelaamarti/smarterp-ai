"use client";

import { useKpis } from "@/hooks/useKpis";
import { KPICard } from "./KPICard";

export function KPIGrid() {
  const { data: kpis, isLoading, isError, error } = useKpis();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-xl border border-gray-200 bg-gray-100"
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
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {kpis?.map((kpi) => (
        <KPICard key={kpi.id} kpi={kpi} />
      ))}
    </div>
  );
}
