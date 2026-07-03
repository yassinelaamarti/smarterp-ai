import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { KPI } from "@/types";

interface KPICardProps {
  kpi: KPI;
}

const trendConfig = {
  up: { icon: TrendingUp, color: "text-emerald-600 bg-emerald-50" },
  down: { icon: TrendingDown, color: "text-red-600 bg-red-50" },
  stable: { icon: Minus, color: "text-gray-500 bg-gray-100" },
};

export function KPICard({ kpi }: KPICardProps) {
  const trend = kpi.trend ? trendConfig[kpi.trend] : null;
  const TrendIcon = trend?.icon;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{kpi.label}</p>

      <div className="mt-2 flex items-baseline gap-1">
        <span className="text-2xl font-semibold text-gray-900">
          {kpi.value.toLocaleString("fr-FR")}
        </span>
        {kpi.unit && (
          <span className="text-sm text-gray-500">{kpi.unit}</span>
        )}
      </div>

      {trend && TrendIcon && kpi.changePercent !== undefined && (
        <div
          className={cn(
            "mt-3 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
            trend.color
          )}
        >
          <TrendIcon className="h-3.5 w-3.5" />
          <span>
            {kpi.changePercent > 0 ? "+" : ""}
            {kpi.changePercent}%
          </span>
        </div>
      )}
    </div>
  );
}
