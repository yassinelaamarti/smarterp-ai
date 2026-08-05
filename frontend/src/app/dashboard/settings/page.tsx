"use client";

import React, { useState, useEffect } from "react";
import {
  Package,
  TrendingUp,
  Users,
  CheckCircle,
  Save,
  RefreshCw,
  AlertTriangle,
  Mail,
  Calendar,
  Send,
  CreditCard,
  TrendingDown,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useSettings, AlertSetting } from "@/hooks/useSettings";
import { useReportSchedule } from "@/hooks/useReportSchedule";

export default function SettingsPage() {
  const queryClient = useQueryClient();

  const {
    settings,
    isLoading,
    save,
    isSaving,
    isSaveSuccess,
    error,
    resetSaveState,
  } = useSettings();

  const {
    schedule: reportSchedule,
    isLoading: isReportLoading,
    save: saveReportSchedule,
    isSaving: isSavingReport,
    isSaveSuccess: isReportSaveSuccess,
    triggerTest: triggerTestReport,
    isTesting: isTestingReport,
    testSuccess: testReportSuccess,
    resetTestState: resetTestState,
    resetSaveState: resetReportSaveState,
  } = useReportSchedule();

  const [localSettings, setLocalSettings] = useState<AlertSetting[]>([]);
  const [resetSuccess, setResetSuccess] = useState(false);

  const [reportEmail, setReportEmail] = useState("");
  const [reportPeriod, setReportPeriod] = useState<"none" | "daily" | "weekly" | "monthly">("none");

  useEffect(() => {
    if (settings) {
      setLocalSettings(JSON.parse(JSON.stringify(settings)));
    }
  }, [settings]);

  useEffect(() => {
    if (reportSchedule) {
      setReportEmail(reportSchedule.report_email || "");
      setReportPeriod(reportSchedule.report_schedule || "none");
    }
  }, [reportSchedule]);

  useEffect(() => {
    if (isReportSaveSuccess) {
      const timer = setTimeout(() => {
        resetReportSaveState();
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [isReportSaveSuccess, resetReportSaveState]);

  useEffect(() => {
    if (testReportSuccess) {
      const timer = setTimeout(() => {
        resetTestState();
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [testReportSuccess, resetTestState]);

  useEffect(() => {
    if (isSaveSuccess) {
      const timer = setTimeout(() => {
        resetSaveState();
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [isSaveSuccess, resetSaveState]);

  useEffect(() => {
    if (resetSuccess) {
      const timer = setTimeout(() => {
        setResetSuccess(false);
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [resetSuccess]);

  const handleChange = (key: string, value: number) => {
    setLocalSettings((prev) => {
      const exists = prev.some((s) => s.key === key);
      if (exists) {
        return prev.map((s) => (s.key === key ? { ...s, value } : s));
      }
      return [...prev, { key, value, label: key }];
    });
  };

  const getSetting = (key: string) => {
    const s = localSettings.find((item) => item.key === key);
    if (s) return s;
    // Fallbacks si la clé n'est pas encore initialisée dans le state
    if (key === "unpaid_invoices_60_plus_warning") return { key, value: 20, label: "Impayés > 60j (Avertissement)" };
    if (key === "unpaid_invoices_60_plus_critical") return { key, value: 40, label: "Impayés > 60j (Critique)" };
    if (key === "recommendation_acknowledgment_ttl_hours") return { key, value: 24, label: "Délai de rappel des recommandations acquittées" };
    return null;
  };

  // Validation fonctionnelle des paires de seuils
  const validateForm = (): string[] => {
    const errors: string[] = [];

    const getVal = (k: string, defaultVal: number) => {
      const item = getSetting(k);
      return item !== null && item !== undefined ? item.value : defaultVal;
    };

    // 0. Délai de rappel recommandations (>= 0.001h / ~3,6s)
    if (getVal("recommendation_acknowledgment_ttl_hours", 24) < 0.001) {
      errors.push("Rappel des recommandations : le délai doit être d'au moins 0.001 heure (~3,6 secondes).");
    }

    // 1. Stock (Warning <= Critical)
    if (getVal("stock_warning", 0) > getVal("stock_critical", 10)) {
      errors.push("Stock : le seuil d'avertissement ne peut pas être supérieur au seuil critique.");
    }

    // 2. Commandes en retard (Warning <= Critical)
    if (getVal("late_orders_warning", 0) > getVal("late_orders_critical", 5)) {
      errors.push("Commandes en retard : le seuil d'avertissement ne peut pas être supérieur au seuil critique.");
    }

    // 3. Impayés > 60j (Warning <= Critical)
    if (getVal("unpaid_invoices_60_plus_warning", 20) > getVal("unpaid_invoices_60_plus_critical", 40)) {
      errors.push("Trésorerie & Impayés : le seuil d'avertissement (20%) ne peut pas dépasser le seuil critique (40%).");
    }

    // 4. Baisse CA (% négatifs : warning doit être supérieur / moins négatif que critical)
    if (getVal("revenue_warning", -5) < getVal("revenue_critical", -15)) {
      errors.push("Chiffre d'affaires : la baisse d'avertissement (-5%) doit être moins sévère que la baisse critique (-15%).");
    }

    // 5. Nouvelles commandes
    if (getVal("new_orders_warning", -20) < getVal("new_orders_critical", -30)) {
      errors.push("Nouvelles commandes : la baisse d'avertissement (-20%) doit être moins sévère que la baisse critique (-30%).");
    }

    // 6. Pipeline CRM
    if (getVal("pipeline_value_warning", -30) < getVal("pipeline_value_critical", -40)) {
      errors.push("Pipeline CRM : la baisse d'avertissement (-30%) doit être moins sévère que la baisse critique (-40%).");
    }

    return errors;
  };

  const validationErrors = validateForm();

  const handleReset = () => {
    if (window.confirm("Voulez-vous vraiment annuler vos modifications non sauvegardées ?")) {
      if (settings) {
        setLocalSettings(JSON.parse(JSON.stringify(settings)));
        setResetSuccess(true);
        resetSaveState();
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validationErrors.length > 0) return;

    setResetSuccess(false);
    save(localSettings);
    saveReportSchedule({
      report_schedule: reportPeriod,
      report_email: reportEmail || null,
    });

    // Invalider immédiatement les requêtes React Query pour mise à jour sans redémarrage
    queryClient.invalidateQueries({ queryKey: ["settings"] });
    queryClient.invalidateQueries({ queryKey: ["alerts"] });
    queryClient.invalidateQueries({ queryKey: ["kpis"] });
  };

  const renderInput = (key: string, label: string, desc: string, unit: string) => {
    const setting = getSetting(key);
    if (!setting) return null;

    const isCritical = key.includes("critical");
    const isPercentageDrop = unit === "%" && key.includes("warning") || key.includes("critical");

    return (
      <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-2xs hover:shadow-xs transition-all duration-200">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <div className="max-w-[80%]">
            <label className="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
              <span className={`inline-block h-2.5 w-2.5 rounded-full ${isCritical ? "bg-red-500 shadow-xs" : "bg-amber-500 shadow-xs"}`} />
              {label}
            </label>
            <p className="mt-1 text-xs text-slate-400 font-medium leading-relaxed">
              {desc}
            </p>
            {key === "revenue_monthly_goal" && (
              <p className="mt-1 text-xs font-bold text-emerald-700 bg-emerald-50 inline-block px-2 py-0.5 rounded border border-emerald-200">
                Affiche : {setting.value.toLocaleString("fr-FR")} MAD / mois
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-1 flex-shrink-0 self-start sm:self-auto">
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                step="1"
                value={setting.value}
                onChange={(e) => handleChange(key, parseFloat(e.target.value) || 0)}
                className="w-20 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-center text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-2xs"
              />
              <span className="text-xs font-semibold text-slate-400 w-8">{unit}</span>
            </div>
            {isPercentageDrop && (
              <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-bold ${setting.value < 0 ? "bg-amber-50 text-amber-700 border border-amber-200" : "bg-slate-100 text-slate-600"}`}>
                <TrendingDown className="h-2.5 w-2.5" />
                {setting.value < 0 ? `Baisse max. ${setting.value}%` : `Variat. ${setting.value}%`}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (isLoading || isReportLoading) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-3">
        <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
        <p className="text-sm font-medium text-slate-400">Chargement de la configuration...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Configuration</h1>
          <p className="mt-1 text-sm text-slate-500">
            Ajustez les seuils de déclenchement des alertes d'avertissement et critiques de SmartERP AI
          </p>
        </div>
      </div>

      {error && (
        <div className="mt-6 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>Erreur de chargement : {(error as Error).message}</span>
        </div>
      )}

      {/* Floating Success Toast */}
      {(isSaveSuccess || isReportSaveSuccess || resetSuccess || testReportSuccess) && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 rounded-xl border border-slate-200 bg-white/95 backdrop-blur-md px-4 py-3 text-sm font-semibold shadow-lg max-w-md w-[90%] sm:w-auto animate-fadeIn transition-all duration-300">
          <CheckCircle className={`h-5 w-5 flex-shrink-0 ${isSaveSuccess || isReportSaveSuccess || testReportSuccess ? "text-emerald-600" : "text-blue-600"}`} />
          <div className="text-left">
            <p className="font-semibold text-slate-800">
              {testReportSuccess
                ? "Test d'envoi réussi !"
                : isSaveSuccess || isReportSaveSuccess
                  ? "Sauvegarde réussie !"
                  : "Réinitialisation réussie !"}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              {testReportSuccess
                ? "Le rapport PDF de test a été généré et envoyé à l'adresse de réception."
                : isSaveSuccess || isReportSaveSuccess
                  ? "La configuration a été mise à jour et appliquée immédiatement au tableau de bord."
                  : "Les valeurs enregistrées ont été restaurées."}
            </p>
          </div>
        </div>
      )}

      {/* Validation Errors Banner */}
      {validationErrors.length > 0 && (
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50/80 p-4 text-xs text-red-800 space-y-1.5 animate-fadeIn">
          <div className="flex items-center gap-2 font-bold text-red-900 text-sm mb-1">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            Incohérences de seuils détectées (Sauvegarde bloquée)
          </div>
          <ul className="list-disc pl-5 space-y-1 font-semibold">
            {validationErrors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        {/* Section 1: Stocks & Livraisons */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Package className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Alertes Opérationnelles (Stocks & Livraisons)</h2>
              <p className="text-[11px] text-slate-400 font-medium">Configurez les seuils d'alertes absolus sur vos volumes de stocks et retards</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {renderInput("stock_warning", "Stock bas (Avertissement)", "Déclenché quand le nombre de produits en rupture imminente dépasse ce seuil.", "prod.")}
            {renderInput("stock_critical", "Stock critique (Critique)", "Seuil critique recommandé en cas de rupture de stock sur de nombreux produits.", "prod.")}
            {renderInput("late_orders_warning", "Commandes en retard (Avertissement)", "Alerte de surveillance pour le retard des bons de livraison.", "cmd.")}
            {renderInput("late_orders_critical", "Commandes en retard (Critique)", "Seuil d'urgence impactant fortement la satisfaction de vos clients.", "cmd.")}
            {renderInput("recommendation_acknowledgment_ttl_hours", "Rappel des recommandations acquittées (Délai)", "Délai (en heures) après lequel une recommandation marquée comme lue repasse en attente si l'anomalie persiste sans résolution.", "heures")}
          </div>
        </div>

        {/* Section 2: Trésorerie & Facturation */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
              <CreditCard className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Trésorerie & Factures Impayées</h2>
              <p className="text-[11px] text-slate-400 font-medium">Seuils basés sur la proportion d'encours impayé à plus de 60 jours de retard</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {renderInput("unpaid_invoices_60_plus_warning", "Impayés > 60 jours (Avertissement)", "Pourcentage d'encours impayé de plus de 60j déclenchant une alerte de relance.", "%")}
            {renderInput("unpaid_invoices_60_plus_critical", "Impayés > 60 jours (Critique)", "Seuil critique de créances douteuses nécessitant un recouvrement immédiat.", "%")}
          </div>
        </div>

        {/* Section 3: Chiffre d'Affaires & Ventes */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <TrendingUp className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Tendances de Vente (Chiffre d'affaires & Commandes)</h2>
              <p className="text-[11px] text-slate-400 font-medium">Définissez les seuils négatifs de baisse d'activité mensuelle (%)</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {renderInput("revenue_monthly_goal", "Objectif mensuel de Chiffre d'affaires", "Montant cible pour le tracker d'objectif sur le tableau de bord.", "MAD")}
            {renderInput("revenue_warning", "Baisse du Chiffre d'affaires (Avertissement)", "Baisse tolérée avant l'émission d'un signalement de ralentissement des ventes.", "%")}
            {renderInput("revenue_critical", "Chiffre d'affaires en chute (Critique)", "Seuil critique de baisse mensuelle nécessitant un audit financier rapide.", "%")}
            {renderInput("new_orders_warning", "Nouvelles commandes (Avertissement)", "Fléchissement du rythme de signature ou de création de bons de commande.", "%")}
            {renderInput("new_orders_critical", "Chute des commandes (Critique)", "Ralentissement commercial important sur la génération de commandes.", "%")}
          </div>
        </div>

        {/* Section 4: Taux de Conversion & CRM */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
              <Users className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Taux de Conversion & Pipeline CRM</h2>
              <p className="text-[11px] text-slate-400 font-medium">Paramétrez les alertes liées au taux d'acquisition et clients actifs</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {renderInput("conversion_rate_warning", "Taux de conversion (Avertissement)", "Léger ralentissement de la transformation des opportunités en clients.", "%")}
            {renderInput("conversion_rate_critical", "Taux de conversion (Critique)", "Chute importante de l'efficacité commerciale.", "%")}
            {renderInput("pipeline_value_warning", "Valeur du pipeline CRM (Avertissement)", "Baisse de valeur totale cumulée des leads en cours d'opportunités.", "%")}
            {renderInput("pipeline_value_critical", "Valeur du pipeline (Critique)", "Vide important sur les futures rentrées potentielles.", "%")}
            {renderInput("active_customers_warning", "Clients actifs (Avertissement)", "Perte de dynamisme ou baisse du nombre de clients facturés ce mois.", "%")}
            {renderInput("active_customers_critical", "Clients actifs (Critique)", "Désengagement client nécessitant des actions de fidélisation.", "%")}
          </div>
        </div>

        {/* Section 5: Rapports Programmés par E-mail (Styling distinct) */}
        <div className="rounded-2xl border-2 border-indigo-200/90 bg-gradient-to-br from-indigo-50/40 via-white to-violet-50/40 p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-indigo-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
              <Mail className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-indigo-950">Rapports Stratégiques Programmés (PDF)</h2>
              <p className="text-[11px] text-indigo-700/70 font-medium">Configurez l'envoi automatique de rapports de synthèse décisionnelle au format PDF</p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Email de destination */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Adresse e-mail de réception
              </label>
              <div className="relative rounded-lg shadow-2xs">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  value={reportEmail}
                  onChange={(e) => setReportEmail(e.target.value)}
                  placeholder="directeur@smarterp.ai"
                  className="block w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium placeholder-slate-400"
                />
              </div>
              <p className="text-[10px] text-slate-400 font-medium">
                Si ce champ est vide, les rapports seront envoyés à l'adresse de votre compte principal.
              </p>
            </div>

            {/* Périodicité */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Fréquence de planification
              </label>
              <div className="relative rounded-lg shadow-2xs">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                  <Calendar className="h-4 w-4" />
                </div>
                <select
                  value={reportPeriod}
                  onChange={(e) => setReportPeriod(e.target.value as any)}
                  className="block w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium cursor-pointer"
                >
                  <option value="none">Désactivé</option>
                  <option value="daily">Quotidien (Pour tests)</option>
                  <option value="weekly">Hebdomadaire</option>
                  <option value="monthly">Mensuel</option>
                </select>
              </div>
              <p className="text-[10px] text-slate-400 font-medium">
                Les rapports seront générés automatiquement et envoyés à la fréquence sélectionnée sans altérer le test manuel.
              </p>
            </div>
          </div>

          {/* Bouton de test immédiat */}
          <div className="mt-6 pt-4 border-t border-indigo-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="text-xs text-indigo-900/80 font-medium">
              Vous souhaitez valider l'envoi immédiatement ? Lancez une simulation ou un test réel.
            </div>
            <button
              type="button"
              onClick={() => triggerTestReport()}
              disabled={isTestingReport}
              className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-indigo-200 bg-white hover:bg-indigo-50 text-xs font-bold text-indigo-800 px-4 py-2 transition-all cursor-pointer disabled:opacity-50 shadow-2xs"
            >
              {isTestingReport ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-indigo-600" />
                  Génération du PDF...
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5 text-indigo-600" />
                  Tester l'envoi immédiat
                </>
              )}
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 mt-8 border-t border-slate-150 pt-6">
          <button
            type="button"
            onClick={handleReset}
            disabled={isSaving}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer disabled:opacity-50"
          >
            Réinitialiser les modifications
          </button>

          <button
            type="submit"
            disabled={isSaving || validationErrors.length > 0}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-500/10 hover:from-blue-500 hover:to-indigo-500 transition-all cursor-pointer disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Enregistrement...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Sauvegarder la configuration
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
