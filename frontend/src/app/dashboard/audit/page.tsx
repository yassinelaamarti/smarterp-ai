"use client";

import React, { useState, useMemo } from "react";
import { useRecommendationsAudit } from "@/hooks/useRecommendations";
import {
  ShieldAlert,
  Loader2,
  Calendar,
  User,
  CheckCircle2,
  XCircle,
  Package,
  Mail,
  Users,
  Clock,
  Search,
  ChevronDown,
  ChevronUp,
  FileCode2,
  Eye,
  AlertTriangle,
} from "lucide-react";

export default function AuditPage() {
  const { data: auditLogs, isLoading, error } = useRecommendationsAudit();

  // Etats pour filtres et recherche
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedActionType, setSelectedActionType] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedPeriod, setSelectedPeriod] = useState<string>("all");

  // Etat pour lignes avec détails techniques dépliés (set d'IDs)
  const [expandedTechIds, setExpandedTechIds] = useState<Set<string>>(new Set());

  const toggleTechDetails = (id: string) => {
    setExpandedTechIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Formatage propre et métier des erreurs techniques brutes
  const formatBusinessError = (rawError?: string) => {
    if (!rawError) return "Erreur d'exécution Odoo";
    const err = rawError.toLowerCase();

    if (err.includes("entier superieur a 0") || err.includes("entier")) {
      return "Rejet par le garde-fou : La quantité à commander doit être un nombre entier valide (supérieur à 0).";
    }
    if (err.includes("rate limit") || err.includes("429")) {
      return "Quota LLM temporairement atteint (Rate limit API) : Basculement automatique sur la règle métier déterministe.";
    }
    if (err.includes("partner_ids") || err.includes("n'existent pas dans odoo")) {
      return "Contrôle d'intégrité Odoo : Les identifiants partenaires (partner_ids) sont introuvables ou invalides dans Odoo.";
    }
    if (err.includes("aucun commercial") || err.includes("user_id")) {
      return "Garde-fou de responsabilité : La commande n'a aucun commercial assigné dans Odoo — action non réalisable automatiquement.";
    }
    if (err.includes("n'existe pas dans odoo")) {
      return "Contrôle d'existence Odoo : L'enregistrement spécifié n'existe pas dans la base Odoo.";
    }

    return `Erreur d'intégration Odoo : ${rawError}`;
  };

  // Filtrage combiné des logs d'audit
  const filteredLogs = useMemo(() => {
    if (!auditLogs) return [];

    const now = new Date();

    return auditLogs.filter((log) => {
      // 1. Filtre par type d'action
      if (selectedActionType !== "all") {
        if (selectedActionType === "none" && log.actionType !== "none") return false;
        if (selectedActionType !== "none" && log.actionType !== selectedActionType) return false;
      }

      // 2. Filtre par statut
      if (selectedStatus !== "all") {
        const isDismissed = log.status === "dismissed" || log.success === null || log.odooResult?.info?.includes("ignorée");
        const isFailed = (log.status === "failed" || log.success === false) && !isDismissed;
        const isExecuted = (log.status === "executed" || log.success === true) && !isDismissed && log.actionType !== "none";
        const isAcknowledged = log.actionType === "none" || log.status === "acknowledged";

        if (selectedStatus === "success" && !isExecuted) return false;
        if (selectedStatus === "dismissed" && !isDismissed) return false;
        if (selectedStatus === "acknowledged" && !isAcknowledged) return false;
        if (selectedStatus === "failed" && !isFailed) return false;
      }

      // 3. Filtre par période
      if (selectedPeriod !== "all" && log.executedAt) {
        const execDate = new Date(log.executedAt);
        const diffHours = (now.getTime() - execDate.getTime()) / (1000 * 3600);
        if (selectedPeriod === "today" && diffHours > 24) return false;
        if (selectedPeriod === "7d" && diffHours > 24 * 7) return false;
        if (selectedPeriod === "30d" && diffHours > 24 * 30) return false;
      }

      // 4. Recherche textuelle libre
      if (searchTerm.trim() !== "") {
        const query = searchTerm.toLowerCase();
        const titleMatch = log.title?.toLowerCase().includes(query);
        const userMatch = log.executedByName?.toLowerCase().includes(query);
        const actionMatch = log.actionType?.toLowerCase().includes(query);
        const payloadMatch = JSON.stringify(log.actionPayload || {}).toLowerCase().includes(query);
        const errorMatch = log.errorMessage?.toLowerCase().includes(query);
        const odooMatch = JSON.stringify(log.odooResult || {}).toLowerCase().includes(query);

        if (!titleMatch && !userMatch && !actionMatch && !payloadMatch && !errorMatch && !odooMatch) {
          return false;
        }
      }

      return true;
    });
  }, [auditLogs, selectedActionType, selectedStatus, selectedPeriod, searchTerm]);

  // Statistiques rapides exactes et cohérentes à 100%
  const stats = useMemo(() => {
    if (!auditLogs) return { total: 0, successCount: 0, dismissedCount: 0, failedCount: 0, acknowledgedCount: 0 };

    return {
      total: auditLogs.length,
      successCount: auditLogs.filter((l) => (l.status === "executed" || l.success === true) && l.status !== "dismissed" && l.success !== null && !l.odooResult?.info?.includes("ignorée") && l.actionType !== "none").length,
      dismissedCount: auditLogs.filter((l) => l.status === "dismissed" || l.success === null || l.odooResult?.info?.includes("ignorée")).length,
      acknowledgedCount: auditLogs.filter((l) => l.actionType === "none" || l.status === "acknowledged").length,
      failedCount: auditLogs.filter((l) => (l.status === "failed" || l.success === false) && l.status !== "dismissed" && l.success !== null && !l.odooResult?.info?.includes("ignorée")).length,
    };
  }, [auditLogs]);

  // Gestion des clics sur les cartes KPI pour filtrer automatiquement
  const applyQuickFilter = (type: "all" | "success" | "dismissed" | "acknowledged" | "failed") => {
    if (type === "all") {
      setSelectedActionType("all");
      setSelectedStatus("all");
    } else if (type === "success") {
      setSelectedActionType("all");
      setSelectedStatus("success");
    } else if (type === "dismissed") {
      setSelectedActionType("all");
      setSelectedStatus("dismissed");
    } else if (type === "acknowledged") {
      setSelectedActionType("none");
      setSelectedStatus("all");
    } else if (type === "failed") {
      setSelectedActionType("all");
      setSelectedStatus("failed");
    }
  };

  // Icône du type d'action
  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case "restock_order":
        return <Package className="h-4 w-4 text-amber-600 shrink-0" />;
      case "send_email_campaign":
        return <Mail className="h-4 w-4 text-blue-600 shrink-0" />;
      case "create_follow_up_activity":
        return <Clock className="h-4 w-4 text-rose-600 shrink-0" />;
      case "create_crm_activity":
        return <Users className="h-4 w-4 text-purple-600 shrink-0" />;
      default:
        return <Eye className="h-4 w-4 text-indigo-600 shrink-0" />;
    }
  };

  // Libellé métier du type d'action
  const getActionTypeTitle = (actionType: string) => {
    switch (actionType) {
      case "restock_order":
        return "Réapprovisionnement";
      case "send_email_campaign":
        return "Campagne Email";
      case "create_follow_up_activity":
        return "Relance Livraison";
      case "create_crm_activity":
        return "Activité CRM";
      case "none":
        return "Alerte Reconnue";
      default:
        return actionType;
    }
  };

  // Badge d'impact réel (post-exécution ou rejet)
  const getHonestImpactBadge = (log: any) => {
    const isDismissed = log.status === "dismissed" || log.success === null || log.success === undefined || log.odooResult?.info?.includes("ignorée");
    if (isDismissed) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-2xs font-bold text-slate-600">
          <XCircle className="h-3 w-3 text-slate-400 shrink-0" />
          Ignorée
        </span>
      );
    }

    if (log.status === "failed" || log.success === false) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-red-50 border border-red-200 px-2.5 py-0.5 text-2xs font-bold text-red-700">
          <XCircle className="h-3 w-3 text-red-600 shrink-0" />
          Échec d'exécution
        </span>
      );
    }

    switch (log.actionType) {
      case "restock_order":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-2xs font-bold text-amber-750">
            <Package className="h-3 w-3 text-amber-600 shrink-0" />
            Réapprovisionnement demandé
          </span>
        );
      case "send_email_campaign":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 border border-blue-200 px-2.5 py-0.5 text-2xs font-bold text-blue-750">
            <Mail className="h-3 w-3 text-blue-600 shrink-0" />
            Client(s) contacté(s)
          </span>
        );
      case "create_follow_up_activity":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 border border-rose-200 px-2.5 py-0.5 text-2xs font-bold text-rose-750">
            <Clock className="h-3 w-3 text-rose-600 shrink-0" />
            Relance planifiée
          </span>
        );
      case "create_crm_activity":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-purple-50 border border-purple-200 px-2.5 py-0.5 text-2xs font-bold text-purple-750">
            <Users className="h-3 w-3 text-purple-600 shrink-0" />
            Tâche CRM enregistrée
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 text-2xs font-bold text-indigo-750">
            <CheckCircle2 className="h-3 w-3 text-indigo-600 shrink-0" />
            Alerte prise en compte
          </span>
        );
    }
  };

  // Titre nettoyé pour les alertes reconnues
  const getCleanTitle = (log: any) => {
    let title = log.title || "Alerte de pilotage";
    if (log.actionType === "none") {
      const clean = title.replace(/^Analyse IA temporairement indisponible —\s*/i, "").replace(/^Aucune action requise pour\s*/i, "");
      return `Alerte reconnue : ${clean}`;
    }
    return title;
  };

  // Phrase business explicite dans la colonne "Détail de l'action"
  const renderBusinessDescription = (log: any) => {
    const p = log.actionPayload || {};
    const odooRes = log.odooResult || {};
    const isDismissed = log.status === "dismissed" || log.success === null || log.success === undefined || odooRes.info?.includes("ignorée");

    if (isDismissed) {
      return (
        <span className="text-slate-500 leading-relaxed italic">
          Recommandation ignorée par l'utilisateur — aucune action exécutée sur Odoo.
        </span>
      );
    }

    if (log.status === "failed" || log.success === false) {
      return (
        <div className="flex items-start gap-1.5 text-red-700 font-medium leading-relaxed">
          <AlertTriangle className="h-3.5 w-3.5 text-red-600 shrink-0 mt-0.5" />
          <span>{formatBusinessError(log.errorMessage)}</span>
        </div>
      );
    }

    switch (log.actionType) {
      case "create_follow_up_activity": {
        const orderId = p.order_id ? `S000${p.order_id}` : p.order_name || "Odoo";
        const salesRep = p.sales_rep_name || (odooRes.message?.includes("assignee a") ? odooRes.message.split("assignee a")[1].replace(".", "").trim() : "Commercial assigné");
        return (
          <span className="text-slate-700 font-medium leading-relaxed">
            Relance créée pour la commande <strong className="text-slate-900 font-semibold">{orderId}</strong>, assignée à <strong className="text-slate-900 font-semibold">{salesRep}</strong>.
          </span>
        );
      }
      case "restock_order": {
        const qty = p.quantity || p.quantity_to_order || 10;
        const prodId = p.product_id ? `#${p.product_id}` : "";
        const odooPo = odooRes.odoo_id ? `(Bon d'achat #${odooRes.odoo_id})` : "";
        return (
          <span className="text-slate-700 font-medium leading-relaxed">
            Bon de commande d'achat brouillon généré dans Odoo pour <strong className="text-slate-900 font-semibold">{qty} unité(s)</strong> du produit {prodId} {odooPo}.
          </span>
        );
      }
      case "send_email_campaign": {
        const partnerCount = p.partner_ids?.length || p.recipients?.length || 1;
        return (
          <span className="text-slate-700 font-medium leading-relaxed">
            Campagne d'emails de relance transmise à <strong className="text-slate-900 font-semibold">{partnerCount} client(s) Odoo</strong> via la file d'attente sortante Odoo.
          </span>
        );
      }
      case "create_crm_activity": {
        return (
          <span className="text-slate-700 font-medium leading-relaxed">
            Activité de suivi CRM enregistrée sur la fiche de lead/opportunité Odoo pour l'équipe commerciale.
          </span>
        );
      }
      default: {
        const cleanKpi = log.title?.replace(/^Analyse IA temporairement indisponible —\s*/i, "") || "KPI";
        return (
          <span className="text-slate-600 leading-relaxed italic">
            Consultation et prise en compte de l'alerte par le dirigeant : <strong className="text-slate-800 not-italic font-semibold">{cleanKpi}</strong>.
          </span>
        );
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        <p className="text-sm font-medium text-slate-400">Chargement du journal d'audit de conformité...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fadeIn pb-12">
      {/* En-tête principal */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Audit des Actions IA</h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Journal de conformité et traçabilité SOC 2 des décisions et exécutions SmartERP AI sur Odoo.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 text-2xs font-bold text-emerald-700">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Traçabilité active
          </span>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2.5 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800">
          <ShieldAlert className="h-4 w-4 flex-shrink-0 text-red-600" />
          <span>Erreur de chargement du registre d'audit : {(error as Error).message}</span>
        </div>
      )}

      {/* Cartes d'indicateurs de gouvernance intéractives */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        <button
          onClick={() => applyQuickFilter("all")}
          className={`text-left rounded-2xl border p-4 shadow-xs transition-all cursor-pointer ${
            selectedActionType === "all" && selectedStatus === "all"
              ? "border-slate-400 bg-slate-100/80 ring-2 ring-slate-400/20"
              : "border-slate-200/80 bg-white hover:bg-slate-50/80"
          }`}
        >
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Événements enregistrés</div>
          <div className="mt-2 text-xl font-extrabold text-slate-900">{stats.total}</div>
        </button>

        <button
          onClick={() => applyQuickFilter("success")}
          className={`text-left rounded-2xl border p-4 shadow-xs transition-all cursor-pointer ${
            selectedStatus === "success"
              ? "border-emerald-500 bg-emerald-100/50 ring-2 ring-emerald-500/20"
              : "border-emerald-100 bg-emerald-50/30 hover:bg-emerald-50/70"
          }`}
        >
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700">Actions Odoo Exécutées</div>
          <div className="mt-2 text-xl font-extrabold text-emerald-800">{stats.successCount}</div>
        </button>

        <button
          onClick={() => applyQuickFilter("dismissed")}
          className={`text-left rounded-2xl border p-4 shadow-xs transition-all cursor-pointer ${
            selectedStatus === "dismissed"
              ? "border-slate-500 bg-slate-200/60 ring-2 ring-slate-400/20"
              : "border-slate-200 bg-slate-50/50 hover:bg-slate-100/60"
          }`}
        >
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-600">Recommandations Ignorées</div>
          <div className="mt-2 text-xl font-extrabold text-slate-800">{stats.dismissedCount}</div>
        </button>

        <button
          onClick={() => applyQuickFilter("acknowledged")}
          className={`text-left rounded-2xl border p-4 shadow-xs transition-all cursor-pointer ${
            selectedActionType === "none"
              ? "border-indigo-500 bg-indigo-100/50 ring-2 ring-indigo-500/20"
              : "border-indigo-100 bg-indigo-50/30 hover:bg-indigo-50/70"
          }`}
        >
          <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-700">Alertes Reconnues</div>
          <div className="mt-2 text-xl font-extrabold text-indigo-800">{stats.acknowledgedCount}</div>
        </button>

        <button
          onClick={() => applyQuickFilter("failed")}
          className={`text-left rounded-2xl border p-4 shadow-xs transition-all cursor-pointer ${
            selectedStatus === "failed"
              ? "border-red-500 bg-red-100/50 ring-2 ring-red-500/20"
              : "border-red-100 bg-red-50/30 hover:bg-red-50/70"
          }`}
        >
          <div className="text-[11px] font-bold uppercase tracking-wider text-red-700">Échecs d'exécution</div>
          <div className="mt-2 text-xl font-extrabold text-red-800">{stats.failedCount}</div>
        </button>
      </div>

      {/* Barre de recherche et filtres de contrôle */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs space-y-3">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Recherche textuelle libre */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Rechercher par commande (S00024), produit, client, commercial ou mot-clé..."
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400"
            />
          </div>

          {/* Filtres déroulants */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Type d'action */}
            <select
              value={selectedActionType}
              onChange={(e) => setSelectedActionType(e.target.value)}
              className="px-3 py-2 text-xs font-semibold border border-slate-200 rounded-xl bg-slate-50/50 hover:bg-slate-100/50 focus:outline-none text-slate-700 cursor-pointer"
            >
              <option value="all">Tous types d'actions</option>
              <option value="restock_order">Réapprovisionnement</option>
              <option value="send_email_campaign">Campagne Email</option>
              <option value="create_follow_up_activity">Relance Livraison</option>
              <option value="create_crm_activity">Activité CRM</option>
              <option value="none">Alerte Reconnue</option>
            </select>

            {/* Statut */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 text-xs font-semibold border border-slate-200 rounded-xl bg-slate-50/50 hover:bg-slate-100/50 focus:outline-none text-slate-700 cursor-pointer"
            >
              <option value="all">Tous les statuts</option>
              <option value="success">Exécutée (Succès)</option>
              <option value="dismissed">Ignorée (Sans écriture Odoo)</option>
              <option value="acknowledged">Reconnue (Consultation)</option>
              <option value="failed">Échouée</option>
            </select>

            {/* Période */}
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="px-3 py-2 text-xs font-semibold border border-slate-200 rounded-xl bg-slate-50/50 hover:bg-slate-100/50 focus:outline-none text-slate-700 cursor-pointer"
            >
              <option value="all">Toute la période</option>
              <option value="today">Aujourd'hui</option>
              <option value="7d">7 derniers jours</option>
              <option value="30d">30 derniers jours</option>
            </select>
          </div>
        </div>
      </div>

      {/* Registre des Logs d'Audit */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-100 p-4 bg-slate-50/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Registre d'Audit SOC 2
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-bold">
            {filteredLogs.length} sur {stats.total} enregistrement(s)
          </span>
        </div>

        {filteredLogs.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center gap-2">
            <ShieldAlert className="h-8 w-8 text-slate-300" />
            <p className="text-sm font-semibold text-slate-700">Aucun enregistrement ne correspond à vos filtres</p>
            <p className="text-xs text-slate-450 max-w-sm">
              Essayez de réinitialiser vos critères de recherche ou cliquez sur "Événements enregistrés" en haut.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/80 text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4 w-40">Date & Horodatage</th>
                  <th className="py-3.5 px-4 w-48">Type & Sujet</th>
                  <th className="py-3.5 px-4 w-44">Décision & Impact</th>
                  <th className="py-3.5 px-4">Détail de l'Action (Business)</th>
                  <th className="py-3.5 px-4 w-36 text-right">Opérateur</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs sm:text-sm">
                {filteredLogs.map((log) => {
                  const isTechExpanded = expandedTechIds.has(log.id);

                  return (
                    <tr key={log.id} className="hover:bg-slate-50/50 transition-colors align-top">
                      {/* Horodatage */}
                      <td className="py-4 px-4 whitespace-nowrap text-slate-500 font-medium">
                        <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                          <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          {log.executedAt ? (
                            new Date(log.executedAt).toLocaleString("fr-FR", {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          ) : (
                            "-"
                          )}
                        </div>
                      </td>

                      {/* Type d'action & Sujet */}
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-1.5 font-bold text-slate-800 text-xs">
                          {getActionIcon(log.actionType)}
                          <span>{getActionTypeTitle(log.actionType)}</span>
                        </div>
                        <div className="text-[11px] text-slate-500 font-medium mt-1 leading-snug">
                          {getCleanTitle(log)}
                        </div>
                      </td>

                      {/* Badge d'impact honnête */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        {getHonestImpactBadge(log)}
                      </td>

                      {/* Phrase business & Détails techniques repliables */}
                      <td className="py-4 px-4">
                        <div className="text-xs text-slate-800">
                          {renderBusinessDescription(log)}
                        </div>

                        {/* Bouton repliable pour détails techniques */}
                        <div className="mt-2">
                          <button
                            onClick={() => toggleTechDetails(log.id)}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-indigo-600 transition-colors cursor-pointer"
                          >
                            <FileCode2 className="h-3 w-3" />
                            <span>{isTechExpanded ? "Masquer le JSON technique" : "Voir les détails techniques"}</span>
                            {isTechExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          </button>

                          {/* Bloc JSON / Détails Odoo repliable */}
                          {isTechExpanded && (
                            <div className="mt-2.5 space-y-2 p-3 bg-slate-900 text-slate-200 rounded-xl font-mono text-[10px] leading-relaxed shadow-inner border border-slate-800 animate-fadeIn">
                              <div>
                                <span className="text-cyan-400 font-bold">// Paramètres de la recommandation (Payload) :</span>
                                <pre className="mt-1 text-slate-300 overflow-x-auto whitespace-pre-wrap">
                                  {JSON.stringify(log.actionPayload || {}, null, 2)}
                                </pre>
                              </div>
                              {log.odooResult && (
                                <div className="pt-2 border-t border-slate-800">
                                  <span className="text-emerald-400 font-bold">// Réponse d'intégration Odoo XML-RPC :</span>
                                  <pre className="mt-1 text-emerald-200 overflow-x-auto whitespace-pre-wrap">
                                    {JSON.stringify(log.odooResult, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {log.errorMessage && (
                                <div className="pt-2 border-t border-slate-800 text-red-400">
                                  <span className="font-bold">// Erreur technique d'exécution brute :</span>
                                  <pre className="mt-1 text-red-300 overflow-x-auto whitespace-pre-wrap">
                                    {log.errorMessage}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Opérateur (User) */}
                      <td className="py-4 px-4 whitespace-nowrap text-right text-slate-600 font-medium">
                        <div className="inline-flex items-center gap-1.5 text-xs text-slate-700 font-semibold bg-slate-100/70 border border-slate-200/60 px-2.5 py-1 rounded-lg">
                          <User className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                          <span>{log.executedByName || "Système"}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
