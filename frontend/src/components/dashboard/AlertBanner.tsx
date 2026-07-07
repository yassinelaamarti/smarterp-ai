"use client";

import { AlertTriangle, AlertOctagon, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAlerts } from "@/hooks/useAlerts";

export function AlertBanner() {
  const { data: alerts, isLoading } = useAlerts();
  const router = useRouter();

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
              "flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm backdrop-blur-xl shadow-xs transition-all",
              isCritical
                ? "border-red-100 bg-red-50/70 text-red-950"
                : "border-amber-100 bg-amber-50/70 text-amber-950"
            )}
          >
            <div className="flex items-center gap-3">
              <Icon className={cn("h-4 w-4 flex-shrink-0", isCritical ? "text-red-600" : "text-amber-600")} />
              <span className="font-medium">{alert.message}</span>
            </div>
            <button
              onClick={() => {
                const promptText = `Explique-moi l'alerte suivante : "${alert.message}". Pourquoi cela se produit-il et quelles actions concrètes me conseilles-tu d'entreprendre ?`;
                router.push(`/dashboard/chat?prompt=${encodeURIComponent(promptText)}`);
              }}
              className={cn(
                "flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border transition-all cursor-pointer shadow-xs",
                isCritical
                  ? "border-red-200 bg-white hover:bg-red-50 text-red-700"
                  : "border-amber-200 bg-white hover:bg-amber-50 text-amber-700"
              )}
            >
              Analyser avec l'IA
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
