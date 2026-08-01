"use client";

import { useState } from "react";
import { useKpis } from "@/hooks/useKpis";
import { MetricCard } from "./MetricCard";
import { KPIDetailModal } from "./KPIDetailModal";
import type { KPI } from "@/types";
import { DollarSign, Package, Users } from "lucide-react";


const SECTIONS = [
  {
    id: "sales_finance",
    title: "Ventes & Trésorerie",
    icon: DollarSign,
    kpiIds: ["revenue", "new_orders", "avg_order_value", "unpaid_invoices", "unpaid_invoices_count"],
    color: "text-emerald-700 bg-emerald-50 border-emerald-200",
  },
  {
    id: "stock_ops",
    title: "Stock & Opérations",
    icon: Package,
    kpiIds: ["stock_alerts", "stock_value", "late_orders"],
    color: "text-amber-700 bg-amber-50 border-amber-200",
  },
  {
    id: "crm_customers",
    title: "CRM & Clients",
    icon: Users,
    kpiIds: ["new_leads", "conversion_rate", "pipeline_value", "active_customers"],
    color: "text-blue-700 bg-blue-50 border-blue-200",
  },
];

export function KPIGrid() {
  const { data: kpis, isLoading, isError, error } = useKpis();
  const [selectedKpi, setSelectedKpi] = useState<KPI | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-8">
        {SECTIONS.map((sec) => (
          <div key={sec.id} className="space-y-3">
            <div className="h-6 w-48 animate-pulse rounded bg-slate-200" />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: sec.kpiIds.length }).map((_, i) => (
                <div
                  key={i}
                  className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-slate-100"
                />
              ))}
            </div>
          </div>
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

  const kpiMap = new Map(kpis?.map((k) => [k.id, k]));

  return (
    <>
      <div className="space-y-8">
        {SECTIONS.map((section) => {
          const SectionIcon = section.icon;
          const sectionKpis = section.kpiIds
            .map((id) => kpiMap.get(id))
            .filter((k): k is KPI => k !== undefined);

          if (sectionKpis.length === 0) return null;

          return (
            <div key={section.id} className="space-y-3">
              {/* Titre de section thématique */}
              <div className="flex items-center gap-2 border-b border-slate-200/80 pb-2">
                <div className={`flex h-7 w-7 items-center justify-center rounded-lg border ${section.color}`}>
                  <SectionIcon className="h-4 w-4" />
                </div>
                <h2 className="text-sm font-bold tracking-wide text-slate-800 uppercase">
                  {section.title}
                </h2>
                <span className="ml-auto text-[11px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                  {sectionKpis.length} métriques
                </span>
              </div>

              {/* Grille des cartes de la section */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {sectionKpis.map((kpi) => (
                  <MetricCard key={kpi.id} kpi={kpi} onClick={setSelectedKpi} />
                ))}
              </div>
            </div>
          );
        })}
      </div>
      
      {selectedKpi && (
        <KPIDetailModal kpi={selectedKpi} onClose={() => setSelectedKpi(null)} />
      )}
    </>
  );
}


