"use client";

import React, { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  ShoppingCart,
  ShoppingBag,
  AlertTriangle,
  UserPlus,
  TrendingUp as TrendUpIcon,
  Briefcase,
  Package,
  Users,
  Clock,
  FileText,
  Receipt,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { KPI } from "@/types";
import { useKpiHistory } from "@/hooks/useKpiHistory";
import { AreaChart, Area, ResponsiveContainer, Tooltip } from "recharts";

interface MetricCardProps {
  kpi: KPI;
  onClick?: (kpi: KPI) => void;
}

const trendConfig = {
  up: { icon: TrendingUp, color: "text-emerald-700 bg-emerald-50 border border-emerald-100" },
  down: { icon: TrendingDown, color: "text-red-700 bg-red-50 border border-red-100" },
  stable: { icon: Minus, color: "text-slate-600 bg-slate-50 border border-slate-100" },
};

const kpiIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  revenue: DollarSign,
  new_orders: ShoppingCart,
  avg_order_value: ShoppingBag,
  stock_alerts: AlertTriangle,
  new_leads: UserPlus,
  conversion_rate: TrendUpIcon,
  pipeline_value: Briefcase,
  stock_value: Package,
  active_customers: Users,
  late_orders: Clock,
  unpaid_invoices: FileText,
  unpaid_invoices_count: Receipt,
};

// Classification des KPIs en familles
const FLOW_KPIS = ["revenue", "new_orders", "new_leads", "active_customers", "late_orders"];
const RATIO_KPIS = ["avg_order_value", "conversion_rate"];
const SNAPSHOT_KPIS = ["pipeline_value", "stock_value", "unpaid_invoices", "unpaid_invoices_count", "stock_alerts"];

export function MetricCard({ kpi, onClick }: MetricCardProps) {
  const [period, setPeriod] = useState<"week" | "month" | "trimester">("month");
  const isFlowKpi = FLOW_KPIS.includes(kpi.id);
  const isRatioKpi = RATIO_KPIS.includes(kpi.id);
  const isSnapshotKpi = kpi.isSnapshot || SNAPSHOT_KPIS.includes(kpi.id);

  const { data: historyData } = useKpiHistory(kpi.id, period);

  const trend = kpi.trend ? trendConfig[kpi.trend] : null;
  const TrendIcon = trend?.icon;
  const Icon = kpiIcons[kpi.id] || Package;

  // Hierarchie visuelle par criticité ('normal' | 'attention' | 'critical')
  const criticality = kpi.criticality ?? "normal";

  const cardStyle =
    criticality === "critical"
      ? "bg-red-50/40 border-red-200/90 shadow-sm hover:border-red-300 hover:shadow-red-500/5"
      : criticality === "attention"
      ? "bg-amber-50/40 border-amber-200/80 shadow-sm hover:border-amber-300"
      : "bg-white border-slate-200/80 shadow-sm hover:border-blue-300";

  const iconStyle =
    criticality === "critical"
      ? "bg-red-100/70 text-red-700 border-red-200/60 group-hover:bg-red-100 group-hover:text-red-800"
      : criticality === "attention"
      ? "bg-amber-100/50 text-amber-700 border-amber-200/50 group-hover:bg-amber-100 group-hover:text-amber-800"
      : "bg-slate-50 border-slate-100 group-hover:border-slate-200 group-hover:text-slate-700 text-slate-500";

  const strokeColor =
    criticality === "critical" ? "#dc2626" : criticality === "attention" ? "#d97706" : "#2563eb";
  const fillColor =
    criticality === "critical" ? "#ef4444" : criticality === "attention" ? "#f59e0b" : "#3b82f6";

  // Avertissement d'échantillon réduit sur les ratios
  const isSmallSample =
    kpi.sampleSize !== undefined &&
    kpi.sampleSize < (kpi.sampleWarningThreshold ?? 5);

  return (
    <div
      onClick={() => onClick && onClick(kpi)}
      className={cn(
        "relative flex flex-col justify-between overflow-hidden rounded-2xl border p-5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg group",
        onClick ? "cursor-pointer" : "",
        cardStyle
      )}
    >
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 truncate">
            {kpi.label}
          </span>
          <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-colors duration-200 border", iconStyle)}>
            <Icon className="h-4 w-4" />
          </div>
        </div>

        {/* Value + Trend */}
        <div className="mt-3 flex items-baseline justify-between gap-2">
          <div className="flex flex-col">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black tracking-tight text-slate-900">
                {kpi.value.toLocaleString("fr-FR")}
              </span>
              {kpi.unit && (
                <span className="text-xs font-medium text-slate-500">{kpi.unit}</span>
              )}
            </div>

            {/* Avertissement Petit Échantillon */}
            {isSmallSample && (
              <p className="mt-1 text-[11px] font-medium text-amber-700/80 italic leading-tight">
                Basé sur seulement {kpi.sampleSize} {kpi.sampleUnitLabel || "observations"} — donnée peu représentative
              </p>
            )}
          </div>

          {trend && TrendIcon && kpi.changePercent !== undefined && (
            <div className="flex flex-col items-end shrink-0 self-start">
              <div
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold",
                  trend.color
                )}
              >
                <TrendIcon className="h-3 w-3" />
                <span>
                  {kpi.changePercent > 0 ? "+" : ""}
                  {kpi.changePercent}%
                </span>
              </div>
              {/* Comparaison explicite pour les instantanés */}
              {isSnapshotKpi && (
                <span className="mt-1 text-[10px] font-medium text-slate-400">
                  vs il y a 30 jours
                </span>
              )}
            </div>
          )}
        </div>

        {/* Périodes (Onglets) pour les KPIs de flux/ratio (exclus pour les instantanés) */}
        {(isFlowKpi || isRatioKpi) && !isSnapshotKpi && (
          <div className="mt-3 flex items-center gap-1 border-t border-slate-100 pt-2" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setPeriod("week")}
              className={cn(
                "px-2 py-0.5 text-[10px] font-semibold rounded-md transition-colors",
                period === "week" ? "bg-slate-100 text-blue-700 font-bold" : "text-slate-400 hover:text-slate-600"
              )}
            >
              7j
            </button>
            <button
              onClick={() => setPeriod("month")}
              className={cn(
                "px-2 py-0.5 text-[10px] font-semibold rounded-md transition-colors",
                period === "month" ? "bg-slate-100 text-blue-700 font-bold" : "text-slate-400 hover:text-slate-600"
              )}
            >
              30j
            </button>
            <button
              onClick={() => setPeriod("trimester")}
              className={cn(
                "px-2 py-0.5 text-[10px] font-semibold rounded-md transition-colors",
                period === "trimester" ? "bg-slate-100 text-blue-700 font-bold" : "text-slate-400 hover:text-slate-600"
              )}
            >
              Trim.
            </button>
          </div>
        )}
      </div>


      {/* Sparkline basée sur les VRAIES données historiques */}
      <div className="mt-3 h-10 w-full">
        {historyData && historyData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={historyData} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={`grad-${kpi.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={fillColor} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={fillColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-slate-900 text-white px-2 py-1 rounded text-[10px] shadow">
                        <span>{payload[0].payload.date}: </span>
                        <span className="font-bold">{payload[0].value}</span>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area
                type="stepAfter"
                dataKey="value"
                stroke={strokeColor}
                strokeWidth={2}
                fillOpacity={1}
                fill={`url(#grad-${kpi.id})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full w-full rounded bg-slate-50 border border-dashed border-slate-200" />
        )}
      </div>
    </div>
  );
}

