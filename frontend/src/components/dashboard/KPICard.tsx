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
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { KPI } from "@/types";

interface KPICardProps {
  kpi: KPI;
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
};

export function KPICard({ kpi }: KPICardProps) {
  const trend = kpi.trend ? trendConfig[kpi.trend] : null;
  const TrendIcon = trend?.icon;
  const Icon = kpiIcons[kpi.id] || Package;

  // Custom warning coloring for stock alerts and late orders
  const isAlert = (kpi.id === "stock_alerts" || kpi.id === "late_orders") && kpi.value > 0;

  return (
    <div className={cn(
      "relative overflow-hidden rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md group",
      isAlert 
        ? "bg-amber-50/40 border-amber-200/80 shadow-sm" 
        : "bg-white border-slate-200/80 shadow-sm"
    )}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{kpi.label}</p>
        <div className={cn(
          "flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition-colors duration-200 bg-slate-50 border border-slate-100 group-hover:border-slate-200 group-hover:text-slate-700",
          isAlert && "bg-amber-100/50 text-amber-700 border-amber-200/50 group-hover:bg-amber-100 group-hover:text-amber-800"
        )}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="text-2xl font-bold tracking-tight text-slate-900">
          {kpi.value.toLocaleString("fr-FR")}
        </span>
        {kpi.unit && (
          <span className="text-xs font-medium text-slate-500">{kpi.unit}</span>
        )}
      </div>

      {trend && TrendIcon && kpi.changePercent !== undefined && (
        <div
          className={cn(
            "mt-3 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
            trend.color
          )}
        >
          <TrendIcon className="h-3 w-3" />
          <span>
            {kpi.changePercent > 0 ? "+" : ""}
            {kpi.changePercent}%
          </span>
        </div>
      )}
    </div>
  );
}
