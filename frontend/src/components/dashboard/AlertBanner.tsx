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
              "flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm backdrop-blur-xl",
              isCritical
                ? "border-red-500/20 bg-red-500/10 text-red-300"
                : "border-amber-500/20 bg-amber-500/10 text-amber-300"
            )}
          >
            <div className="flex items-center gap-3">
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span>{alert.message}</span>
            </div>
            <button
              onClick={() => {
                const promptText = `Explique-moi l'alerte suivante : "${alert.message}". Pourquoi cela se produit-il et quelles actions concrètes me conseilles-tu d'entreprendre ?`;
                router.push(`/dashboard/chat?prompt=${encodeURIComponent(promptText)}`);
              }}
              className={cn(
                "flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg border transition-all cursor-pointer",
                isCritical
                  ? "border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-200"
                  : "border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-200"
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
