import React, { useState } from "react";
import {
  Sparkles,
  Eye,
  CheckCircle,
  XCircle,
  TrendingUp,
  Package,
  Mail,
  Users,
  Loader2,
  Check,
  Info,
} from "lucide-react";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useAlerts } from "@/hooks/useAlerts";
import { SourceDataModal } from "./SourceDataModal";
import { RootCauseCard } from "./RootCauseCard";

export function RecommendationsList() {
  const { recommendations, isLoading, execute, dismiss, acknowledge } = useRecommendations();
  const { data: alerts } = useAlerts();

  // Gestion du modal d'explicabilité
  const [selectedSourceData, setSelectedSourceData] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // ID de la recommandation en cours pour le spinner individuel
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [dismissingId, setDismissingId] = useState<string | null>(null);
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const handleExecute = (id: string) => {
    setExecutingId(id);
    execute(id, {
      onSettled: () => setExecutingId(null),
    });
  };

  const handleDismiss = (id: string) => {
    setDismissingId(id);
    dismiss(id, {
      onSettled: () => setDismissingId(null),
    });
  };

  const handleAcknowledge = (id: string) => {
    setAcknowledgingId(id);
    acknowledge(id, {
      onSettled: () => setAcknowledgingId(null),
    });
  };

  const openExplainability = (sourceId: string) => {
    const alert = alerts?.find((a) => a.id === sourceId);
    if (alert && alert.sourceData) {
      setSelectedSourceData(alert.sourceData);
      setIsModalOpen(true);
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case "restock_order":
        return <Package className="h-4 w-4 text-amber-600" />;
      case "send_email_campaign":
        return <Mail className="h-4 w-4 text-blue-600" />;
      case "create_crm_activity":
        return <Users className="h-4 w-4 text-purple-600" />;
      default:
        return <Info className="h-4 w-4 text-indigo-600" />;
    }
  };

  const getActionLabel = (actionType: string, payload?: Record<string, any>) => {
    switch (actionType) {
      case "restock_order":
        return `Commander ${payload?.quantity || 50} unités`;
      case "send_email_campaign":
        return `Campagne Email (${payload?.partner_ids?.length || 0} clients)`;
      case "create_crm_activity":
        return `Planifier Activité CRM`;
      default:
        return "Analyse & Diagnostic Informatif";
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center gap-2 rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
        <span className="text-sm font-medium text-slate-400">Génération des recommandations IA...</span>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return null; // Pas de recommandation -> on n'affiche rien sur le dashboard
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <Sparkles className="h-4 w-4" />
        </div>
        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
          Actions IA recommandées
        </h2>
        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-2xs font-bold text-blue-700">
          {recommendations.length}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendations.map((rec) => {
          const correspondingAlert = alerts?.find((a) => a.id === rec.sourceId || `anomaly_${a.id}` === rec.sourceId);
          const hasExplainability = !!correspondingAlert?.sourceData;
          const isInformative = rec.actionType === "none";
          const anomalyId = correspondingAlert?.id || rec.sourceId.replace("anomaly_", "");

          return (
            <div
              key={rec.id}
              className={`flex flex-col justify-between rounded-2xl border p-5 shadow-xs hover:shadow-md transition-all duration-300 animate-fadeIn ${
                isInformative
                  ? "border-indigo-150 bg-slate-50/40 hover:border-indigo-300"
                  : "border-slate-200/80 bg-white hover:border-slate-350"
              }`}
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-2xs font-bold uppercase ${
                    isInformative
                      ? "bg-indigo-50 border-indigo-200 text-indigo-700"
                      : "bg-slate-50 border-slate-200 text-slate-600"
                  }`}>
                    {getActionIcon(rec.actionType)}
                    {getActionLabel(rec.actionType, rec.actionPayload)}
                  </span>
                  
                  {rec.estimatedImpact && (
                    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-2xs font-bold ${
                      (typeof rec.estimatedImpact === "object" && rec.estimatedImpact.confidence === "high")
                        ? "bg-emerald-50 border border-emerald-100 text-emerald-700"
                        : (typeof rec.estimatedImpact === "object" && rec.estimatedImpact.confidence === "low")
                        ? "bg-amber-50 border border-amber-100 text-amber-700"
                        : "bg-blue-50 border border-blue-100 text-blue-700"
                    }`}>
                      <TrendingUp className="h-3 w-3" />
                      {typeof rec.estimatedImpact === "string" ? rec.estimatedImpact : rec.estimatedImpact.label}
                    </span>
                  )}
                </div>

                {/* Content */}
                <h3 className="mt-3 text-sm font-bold text-slate-800 leading-snug">
                  {rec.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-550">
                  {rec.explanation}
                </p>

                {/* Root Cause Analysis pour les anomalies informatives de KPIs réelles uniquement */}
                {isInformative && hasExplainability && correspondingAlert?.sourceData?.rootCauses && (
                  <div className="mt-3">
                    <RootCauseCard anomalyId={correspondingAlert.id} defaultExpanded={false} />
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                {hasExplainability ? (
                  <button
                    onClick={() => openExplainability(rec.sourceId)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-650 transition-colors cursor-pointer"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Voir la source
                  </button>
                ) : (
                  <div />
                )}

                <div className="flex items-center gap-2">
                  {isInformative ? (
                    <button
                      onClick={() => handleAcknowledge(rec.id)}
                      disabled={acknowledgingId === rec.id}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-xs font-bold text-white px-3.5 py-1.5 transition-all cursor-pointer shadow-2xs shadow-indigo-500/10 hover:shadow-sm disabled:opacity-50"
                    >
                      {acknowledgingId === rec.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Check className="h-3.5 w-3.5" />
                      )}
                      Marquer comme lu
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => handleDismiss(rec.id)}
                        disabled={executingId === rec.id || dismissingId === rec.id}
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-250 hover:bg-slate-50 text-xs font-bold text-slate-650 px-3 py-1.5 transition-all cursor-pointer disabled:opacity-50"
                      >
                        {dismissingId === rec.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <XCircle className="h-3.5 w-3.5 text-slate-400" />
                        )}
                        Ignorer
                      </button>
                      
                      <button
                        onClick={() => handleExecute(rec.id)}
                        disabled={executingId === rec.id || dismissingId === rec.id}
                        className="inline-flex items-center gap-1 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-bold text-white px-3.5 py-1.5 transition-all cursor-pointer shadow-2xs shadow-blue-500/10 hover:shadow-sm disabled:opacity-50"
                      >
                        {executingId === rec.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <CheckCircle className="h-3.5 w-3.5" />
                        )}
                        Exécuter
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {selectedSourceData && (
        <SourceDataModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedSourceData(null);
          }}
          title="Détail du signal Odoo"
          data={selectedSourceData}
        />
      )}
    </div>
  );
}
