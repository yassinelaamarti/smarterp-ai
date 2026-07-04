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
  up: { icon: TrendingUp, color: "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20" },
  down: { icon: TrendingDown, color: "text-red-400 bg-red-500/10 border border-red-500/20" },
  stable: { icon: Minus, color: "text-slate-400 bg-slate-500/10 border border-slate-500/20" },
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
      "relative overflow-hidden rounded-2xl border bg-slate-900/40 p-6 backdrop-blur-xl transition-all duration-300 hover:-translate-y-0.5 hover:bg-slate-900/60 group",
      isAlert 
        ? "border-amber-500/20 hover:border-amber-500/40 hover:shadow-[0_0_20px_rgba(245,158,11,0.05)]" 
        : "border-slate-900 hover:border-slate-800 hover:shadow-[0_0_20px_rgba(99,102,241,0.03)]"
    )}>
      {/* Background card accent glow */}
      <div className={cn(
        "absolute -right-6 -top-6 h-24 w-24 rounded-full blur-2xl opacity-10 transition-opacity duration-300 group-hover:opacity-15",
        isAlert ? "bg-amber-500" : "bg-indigo-500"
      )} />

      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{kpi.label}</p>
        <div className={cn(
          "flex h-9 w-9 items-center justify-center rounded-xl text-slate-300 transition-colors duration-200 bg-slate-950 border border-slate-900 group-hover:border-slate-800 group-hover:text-white",
          isAlert && "text-amber-400 group-hover:text-amber-300"
        )}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="text-2xl font-bold tracking-tight text-white">
          {kpi.value.toLocaleString("fr-FR")}
        </span>
        {kpi.unit && (
          <span className="text-xs font-medium text-slate-400">{kpi.unit}</span>
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
