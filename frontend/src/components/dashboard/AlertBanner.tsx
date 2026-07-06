"use client";

import { AlertTriangle, AlertOctagon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAlerts } from "@/hooks/useAlerts";

export function AlertBanner() {
  const { data: alerts, isLoading } = useAlerts();

  if (isLoading || !alerts || alerts.length === 0) return null;

  return (
    <div className="mb-6 space-y-2">
      {alerts.map((alert) => {
        const isCritical = alert.severity === "critical";
        const Icon = isCritical ? AlertOctagon : AlertTriangle;
        return (
          <div
            key={alert.id}
            className={cn(
              "flex items-center gap-3 rounded-xl border px-4 py-3 text-sm backdrop-blur-xl",
              isCritical
                ? "border-red-500/20 bg-red-500/10 text-red-300"
                : "border-amber-500/20 bg-amber-500/10 text-amber-300"
            )}
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            <span>{alert.message}</span>
          </div>
        );
      })}
    </div>
  );
}
