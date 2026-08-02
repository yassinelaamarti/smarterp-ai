"use client";

import { useState } from "react";
import { AlertTriangle, AlertOctagon, ArrowRight, Brain, Eye, Sparkles, Info } from "lucide-react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAlerts, AlertSourceData } from "@/hooks/useAlerts";
import { SourceDataModal } from "./SourceDataModal";

export function AlertBanner() {
  const { data: alerts, isLoading } = useAlerts();
  const router = useRouter();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedData, setSelectedData] = useState<AlertSourceData | null>(null);
  const [modalTitle, setModalTitle] = useState("");

  if (isLoading || !alerts || alerts.length === 0) return null;

  return (
    <div className="mb-6 space-y-2.5">
      {alerts.map((alert) => {
        const isCritical = alert.severity === "critical";
        const isInfo = alert.severity === "info" || alert.isPositiveTrend;
        const isAnomaly = alert.isAnomaly;

        let containerClass = "border-amber-200/80 bg-amber-50/70 text-amber-950";
        let buttonClass = "border-amber-250 bg-white hover:bg-amber-50 text-amber-800";
        let sourceButtonClass = "border-amber-250 bg-white/60 hover:bg-amber-50 text-amber-700";
        let badgeClass = "bg-amber-100/90 text-amber-900 border-amber-300/70";
        let badgeLabel = "Point d'attention";
        let Icon = AlertTriangle;

        if (isInfo) {
          containerClass = "border-emerald-200/80 bg-emerald-50/70 text-emerald-950";
          buttonClass = "border-emerald-250 bg-white hover:bg-emerald-50 text-emerald-800";
          sourceButtonClass = "border-emerald-250 bg-white/60 hover:bg-emerald-50 text-emerald-700";
          badgeClass = "bg-emerald-100/90 text-emerald-900 border-emerald-300/70";
          badgeLabel = "Audit / Succès";
          Icon = Sparkles;
        } else if (isCritical) {
          containerClass = "border-red-200/80 bg-red-50/70 text-red-950";
          buttonClass = "border-red-250 bg-white hover:bg-red-50 text-red-800";
          sourceButtonClass = "border-red-250 bg-white/60 hover:bg-red-50 text-red-700";
          badgeClass = "bg-red-100/90 text-red-900 border-red-300/70";
          badgeLabel = "Anomalie Critique";
          Icon = AlertOctagon;
        } else if (isAnomaly) {
          containerClass = "border-indigo-200/80 bg-indigo-50/70 text-indigo-950";
          buttonClass = "border-indigo-250 bg-white hover:bg-indigo-50 text-indigo-800";
          sourceButtonClass = "border-indigo-250 bg-white/60 hover:bg-indigo-50 text-indigo-700";
          badgeClass = "bg-indigo-100/90 text-indigo-900 border-indigo-300/70";
          badgeLabel = "Déviation Statistique";
          Icon = Brain;
        }

        return (
          <div
            key={alert.id}
            className={cn(
              "flex flex-col md:flex-row md:items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm backdrop-blur-xl shadow-2xs transition-all",
              containerClass
            )}
          >
            <div className="flex items-center gap-3">
              <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border shadow-2xs flex-shrink-0", badgeClass)}>
                <Icon className="h-3.5 w-3.5" />
                {badgeLabel}
              </span>
              <span className="font-semibold text-xs sm:text-sm leading-relaxed">{alert.message}</span>
            </div>
            
            <div className="flex items-center gap-2 self-end md:self-auto flex-shrink-0">
              {alert.sourceData && (
                <button
                  onClick={() => {
                    const srcData = alert.sourceData
                      ? { ...alert.sourceData, kpiId: alert.kpiId, anomalyId: alert.id }
                      : null;
                    setSelectedData(srcData);
                    setModalTitle(isAnomaly ? "Données Source de l'Anomalie IA" : "Données Source de l'Alerte");
                    setIsModalOpen(true);
                  }}
                  className={cn(
                    "flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border transition-all cursor-pointer shadow-2xs",
                    sourceButtonClass
                  )}
                >
                  <Eye className="h-3.5 w-3.5" />
                  <span>Données source</span>
                </button>
              )}

              <button
                onClick={() => {
                  const promptText = `Explique-moi l'alerte suivante : "${alert.message}". Pourquoi cela se produit-il et quelles actions concrètes me conseilles-tu d'entreprendre ?`;
                  router.push(`/dashboard/chat?prompt=${encodeURIComponent(promptText)}`);
                }}
                className={cn(
                  "flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border transition-all cursor-pointer shadow-2xs",
                  buttonClass
                )}
              >
                <span>Analyser avec l'IA</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        );
      })}

      <SourceDataModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={modalTitle}
        data={selectedData}
      />
    </div>
  );
}
