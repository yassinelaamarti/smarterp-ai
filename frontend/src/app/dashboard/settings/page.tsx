"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Package,
  TrendingUp,
  Users,
  CheckCircle,
  Save,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";
import { useSettings, AlertSetting } from "@/hooks/useSettings";

export default function SettingsPage() {
  const {
    settings,
    isLoading,
    save,
    isSaving,
    isSaveSuccess,
    error,
    resetSaveState,
  } = useSettings();

  const [localSettings, setLocalSettings] = useState<AlertSetting[]>([]);
  const [resetSuccess, setResetSuccess] = useState(false);

  useEffect(() => {
    if (settings) {
      setLocalSettings(JSON.parse(JSON.stringify(settings)));
    }
  }, [settings]);

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
    setLocalSettings((prev) =>
      prev.map((s) => (s.key === key ? { ...s, value } : s))
    );
  };

  const getSetting = (key: string) => localSettings.find((s) => s.key === key);

  const handleReset = () => {
    if (settings) {
      setLocalSettings(JSON.parse(JSON.stringify(settings)));
      setResetSuccess(true);
      resetSaveState();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setResetSuccess(false);
    save(localSettings);
  };


  const renderInput = (key: string, label: string, desc: string, unit: string) => {
    const setting = getSetting(key);
    if (!setting) return null;

    const isCritical = key.includes("critical");

    return (
      <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-2xs hover:shadow-xs transition-all duration-200">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <div className="max-w-[80%]">
            <label className="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
              <span className={`inline-block h-2 w-2 rounded-full ${isCritical ? "bg-red-500" : "bg-amber-500"}`} />
              {label}
            </label>
            <p className="mt-1 text-xs text-slate-400 font-medium leading-relaxed">
              {desc}
            </p>
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0 self-start sm:self-auto">
            <input
              type="number"
              step={key.includes("stock") || key.includes("late") ? "1" : "1"}
              value={setting.value}
              onChange={(e) => handleChange(key, parseFloat(e.target.value) || 0)}
              className="w-20 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-center text-sm font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-2xs"
            />
            <span className="text-xs font-semibold text-slate-400 w-8">{unit}</span>
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
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
            Ajustez les seuils de déclenchement des alertes warning & critical de SmartERP AI
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
      {(isSaveSuccess || resetSuccess) && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 rounded-xl border border-slate-200 bg-white/95 backdrop-blur-md px-4 py-3 text-sm font-semibold shadow-lg max-w-md w-[90%] sm:w-auto animate-fadeIn transition-all duration-300">
          <CheckCircle className={`h-5 w-5 flex-shrink-0 ${isSaveSuccess ? "text-emerald-600" : "text-blue-600"}`} />
          <div className="text-left">
            <p className={`font-semibold ${isSaveSuccess ? "text-slate-800" : "text-slate-800"}`}>
              {isSaveSuccess ? "Sauvegarde réussie !" : "Réinitialisation réussie !"}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              {isSaveSuccess 
                ? "La configuration a été mise à jour et appliquée." 
                : "Les valeurs enregistrées ont été restaurées."}
            </p>
          </div>
        </div>
      )}



      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        {/* Section 1: Stocks & Commandes */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Package className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Alertes Opérationnelles (Stocks & Livraisons)</h2>
              <p className="text-[11px] text-slate-400 font-medium">Configurez les seuils d&apos;alertes absolus sur vos volumes de stocks et retards</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {renderInput("stock_warning", "Stock bas (Avertissement)", "Déclenché quand le nombre de produits en rupture imminente dépasse ce seuil.", "prod.")}
            {renderInput("stock_critical", "Stock critique (Critique)", "Seuil critique recommandé en cas de rupture de stock sur de nombreux produits.", "prod.")}
            {renderInput("late_orders_warning", "Commandes en retard (Avertissement)", "Alerte de surveillance pour le retard des bons de livraison.", "cmd.")}
            {renderInput("late_orders_critical", "Commandes en retard (Critique)", "Seuil d&apos;urgence impactant fortement la satisfaction de vos clients.", "cmd.")}
          </div>
        </div>

        {/* Section 2: Chiffre d'Affaires & Ventes */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <TrendingUp className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Tendances de Vente (Chiffre d&apos;affaires & Commandes)</h2>
              <p className="text-[11px] text-slate-400 font-medium">Définissez les seuils négatifs de baisse d&apos;activité mensuelle (%)</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {renderInput("revenue_warning", "Baisse du Chiffre d&apos;affaires (Avertissement)", "Baisse tolérée avant l&apos;émission d&apos;un signalement de ralentissement des ventes.", "%")}
            {renderInput("revenue_critical", "Chiffre d&apos;affaires en chute (Critique)", "Seuil critique de baisse mensuelle nécessitant un audit financier rapide.", "%")}
            {renderInput("new_orders_warning", "Nouvelles commandes (Avertissement)", "Fléchissement du rythme de signature ou de création de bons de commande.", "%")}
            {renderInput("new_orders_critical", "Chute des commandes (Critique)", "Ralentissement commercial important sur la génération de commandes.", "%")}
          </div>
        </div>

        {/* Section 3: Taux de Conversion & CRM */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
              <Users className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Taux de Conversion & Pipeline CRM</h2>
              <p className="text-[11px] text-slate-400 font-medium">Paramétrez les alertes liées au taux d&apos;acquisition et clients actifs</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {renderInput("conversion_rate_warning", "Taux de conversion (Avertissement)", "Léger ralentissement de la transformation des opportunités en clients.", "%")}
            {renderInput("conversion_rate_critical", "Taux de conversion (Critique)", "Chute importante de l&apos;efficacité commerciale.", "%")}
            {renderInput("pipeline_value_warning", "Valeur du pipeline CRM (Avertissement)", "Baisse de valeur totale cumulée des leads en cours d&apos;opportunités.", "%")}
            {renderInput("pipeline_value_critical", "Valeur du pipeline (Critique)", "Vide important sur les futures rentrées potentielles.", "%")}
            {renderInput("active_customers_warning", "Clients actifs (Avertissement)", "Perte de dynamisme ou baisse du nombre de clients facturés ce mois.", "%")}
            {renderInput("active_customers_critical", "Clients actifs (Critique)", "Désengagement client nécessitant des actions de fidélisation.", "%")}
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
            disabled={isSaving}
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
