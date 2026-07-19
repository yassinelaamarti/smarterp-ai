"use client";

import React from "react";
import { useRecommendationsAudit } from "@/hooks/useRecommendations";
import {
  ShieldAlert,
  Loader2,
  Calendar,
  User,
  CheckCircle,
  XCircle,
  TrendingUp,
  Tag,
  Info,
} from "lucide-react";

export default function AuditPage() {
  const { data: auditLogs, isLoading, error } = useRecommendationsAudit();

  const getStatusBadge = (status: string, success?: boolean) => {
    if (status === "executed" || (status === "pending" && success === true)) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-xs font-bold text-emerald-700">
          <CheckCircle className="h-3 w-3" />
          Exécutée
        </span>
      );
    }
    if (status === "failed" || success === false) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-red-50 border border-red-200 px-2 py-0.5 text-xs font-bold text-red-700">
          <XCircle className="h-3 w-3" />
          Échouée
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-slate-50 border border-slate-200 px-2 py-0.5 text-xs font-bold text-slate-700">
        <XCircle className="h-3 w-3" />
        Ignorée
      </span>
    );
  };

  const getSourceBadge = (sourceType: string) => {
    switch (sourceType) {
      case "anomaly":
        return "Anomalie IA";
      case "kpi_alert":
        return "Alerte Seuil";
      case "health_score":
        return "Score de Santé";
      default:
        return sourceType;
    }
  };

  const getActionTypeLabel = (actionType: string) => {
    switch (actionType) {
      case "restock_order":
        return "Réapprovisionnement";
      case "send_email_campaign":
        return "Relance Client (Email)";
      case "create_crm_activity":
        return "Planifier tâche CRM";
      default:
        return actionType;
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        <p className="text-sm font-medium text-slate-400">Chargement de l'audit de sécurité...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Audit des Actions IA</h1>
        <p className="mt-1 text-sm text-slate-500">
          Consultez l&apos;historique complet de traçabilité et d&apos;exécution des recommandations SmartERP AI sur Odoo.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <ShieldAlert className="h-4 w-4 flex-shrink-0" />
          <span>Erreur de chargement de l&apos;audit : {(error as Error).message}</span>
        </div>
      )}

      {/* Audit Log Table/Cards */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-100 p-5 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Logs d&apos;activité
            </h2>
          </div>
          <span className="text-xs text-slate-450 font-bold">
            {auditLogs?.length || 0} enregistrements
          </span>
        </div>

        {!auditLogs || auditLogs.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center gap-2">
            <ShieldAlert className="h-8 w-8 text-slate-300" />
            <p className="text-sm font-semibold text-slate-700">Aucune action auditée</p>
            <p className="text-xs text-slate-450 max-w-sm">
              Les actions exécutées ou ignorées par les utilisateurs apparaîtront ici pour des raisons de conformité.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-5">Date d&apos;action</th>
                  <th className="py-3 px-5">Décision / Titre</th>
                  <th className="py-3 px-5">Type d&apos;action</th>
                  <th className="py-3 px-5">Statut</th>
                  <th className="py-3 px-5">Opérateur</th>
                  <th className="py-3 px-5">Paramètres Odoo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs sm:text-sm">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                    {/* Date */}
                    <td className="py-4 px-5 whitespace-nowrap text-slate-450 font-semibold">
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <Calendar className="h-3.5 w-3.5" />
                        {log.executedAt ? new Date(log.executedAt).toLocaleString("fr-FR", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        }) : "-"}
                      </div>
                    </td>

                    {/* Title & Explanation */}
                    <td className="py-4 px-5 max-w-xs">
                      <div className="font-bold text-slate-800">{log.title}</div>
                      <div className="text-[10px] sm:text-xs text-slate-450 mt-1 flex items-center gap-1">
                        <Tag className="h-3 w-3 text-slate-350" />
                        {getSourceBadge(log.sourceType)}
                        {log.estimatedImpact && (
                          <span className="flex items-center gap-0.5 ml-2 font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-100">
                            <TrendingUp className="h-2.5 w-2.5" />
                            {typeof log.estimatedImpact === "string" ? log.estimatedImpact : log.estimatedImpact.label}
                          </span>
                        )}
                      </div>
                      {log.errorMessage && (
                        <div className="mt-2 text-[10px] text-red-700 bg-red-550/10 border border-red-100/50 p-1.5 rounded-lg font-mono leading-normal">
                          <span className="font-bold text-red-800">Erreur :</span> {log.errorMessage}
                        </div>
                      )}
                    </td>

                    {/* Action Type */}
                    <td className="py-4 px-5 whitespace-nowrap text-slate-700 font-semibold">
                      {getActionTypeLabel(log.actionType)}
                    </td>

                    {/* Status */}
                    <td className="py-4 px-5 whitespace-nowrap">
                      {getStatusBadge(log.status, log.success)}
                    </td>

                    {/* Operator */}
                    <td className="py-4 px-5 whitespace-nowrap text-slate-600 font-semibold">
                      <div className="flex items-center gap-1">
                        <User className="h-3.5 w-3.5 text-slate-400" />
                        {log.executedByName || "Système"}
                      </div>
                    </td>

                    {/* Parameters payload */}
                    <td className="py-4 px-5 max-w-xs">
                      {log.actionPayload && Object.keys(log.actionPayload).length > 0 ? (
                        <div className="bg-slate-900 text-slate-200 p-2.5 rounded-lg font-mono text-[10px] overflow-x-auto shadow-inner border border-slate-800">
                          {Object.entries(log.actionPayload).map(([k, v]) => (
                            <div key={k}>
                              <span className="text-cyan-400">{k}:</span> {JSON.stringify(v)}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 font-semibold italic">Aucun paramètre</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
