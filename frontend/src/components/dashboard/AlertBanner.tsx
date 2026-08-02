"use client";

import { useState } from "react";
import { AlertTriangle, AlertOctagon, ArrowRight, Brain, Eye } from "lucide-react";
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
    <div className="mb-6 space-y-2">
      {alerts.map((alert) => {
        const isCritical = alert.severity === "critical";
        const isAnomaly = alert.isAnomaly;

        let containerClass = "border-amber-100 bg-amber-50/70 text-amber-950";
        let buttonClass = "border-amber-200 bg-white hover:bg-amber-50 text-amber-700";
        let sourceButtonClass = "border-amber-250 bg-white/50 hover:bg-amber-50 text-amber-600";
        let iconClass = "text-amber-600";
        let Icon = AlertTriangle;

        if (isAnomaly) {
          containerClass = "border-violet-100 bg-violet-50/70 text-violet-950";
          buttonClass = "border-violet-200 bg-white hover:bg-violet-50 text-violet-700";
          sourceButtonClass = "border-violet-250 bg-white/50 hover:bg-violet-50 text-violet-600";
          iconClass = "text-violet-600";
          Icon = Brain;
        } else if (isCritical) {
          containerClass = "border-red-100 bg-red-50/70 text-red-950";
          buttonClass = "border-red-200 bg-white hover:bg-red-50 text-red-700";
          sourceButtonClass = "border-red-250 bg-white/50 hover:bg-red-50 text-red-600";
          iconClass = "text-red-600";
          Icon = AlertOctagon;
        }

        return (
          <div
            key={alert.id}
            className={cn(
              "flex flex-col md:flex-row md:items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm backdrop-blur-xl shadow-xs transition-all",
              containerClass
            )}
          >
            <div className="flex items-center gap-3">
              <Icon className={cn("h-4 w-4 flex-shrink-0", iconClass)} />
              <span className="font-medium">{alert.message}</span>
            </div>
            
            <div className="flex items-center gap-2 self-end md:self-auto">
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
                    "flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border transition-all cursor-pointer shadow-xs",
                    sourceButtonClass
                  )}
                >
                  <Eye className="h-3.5 w-3.5" />
                  Voir les données source
                </button>
              )}


              <button
                onClick={() => {
                  const promptText = `Explique-moi l'alerte suivante : "${alert.message}". Pourquoi cela se produit-il et quelles actions concrètes me conseilles-tu d'entreprendre ?`;
                  router.push(`/dashboard/chat?prompt=${encodeURIComponent(promptText)}`);
                }}
                className={cn(
                  "flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border transition-all cursor-pointer shadow-xs",
                  buttonClass
                )}
              >
                Analyser avec l'IA
                <ArrowRight className="h-3 w-3" />
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

