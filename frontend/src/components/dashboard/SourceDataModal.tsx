"use client";

import React, { useEffect, useRef, useState } from "react";
import { X, Database, Settings, Activity, Clock, FileCode, CheckCircle, ChevronDown, ChevronUp, Info } from "lucide-react";
import { translateOdooModel, translateOdooDomain } from "@/lib/utils";
import { RootCauseCard } from "./RootCauseCard";

interface SourceData {
  kpiId?: string;
  anomalyId?: string;
  kpiLabel: string;
  kpiValue: number;
  kpiUnit?: string;
  model: string;
  domain: string;
  formula: string;
  thresholdInfo?: string;
  historyValues?: number[];
  zScore?: number;
  mean?: number;
  rootCauses?: string[];
}

interface SourceDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  data: SourceData | null;
}



export function SourceDataModal({ isOpen, onClose, title, data }: SourceDataModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const [showTechnical, setShowTechnical] = useState(false);

  // Prevent scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  // Click outside to close
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, [isOpen, onClose]);

  // Reset technical view toggle when modal reopens
  useEffect(() => {
    if (isOpen) {
      setShowTechnical(false);
    }
  }, [isOpen]);

  if (!isOpen || !data) return null;

  const formatNumber = (val: number) => {
    return new Intl.NumberFormat("fr-FR").format(val);
  };

  const businessFilters = translateOdooDomain(data.domain);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div
        ref={modalRef}
        className="relative flex flex-col w-full max-w-xl max-h-[85vh] bg-white rounded-2xl border border-slate-200 shadow-2xl overflow-hidden transition-all scale-100 animate-scaleIn"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Database className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-slate-800">
                {title}
              </h2>
              <p className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase">
                Traçabilité & Transparence de l'indicateur
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 scrollbar-thin">
          
          {/* Main Metric Banner */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50/50 rounded-xl p-4 border border-blue-100 flex justify-between items-center">
            <div>
              <p className="text-[10px] font-bold text-blue-800 uppercase tracking-wider">Indicateur Odoo</p>
              <h3 className="text-base font-bold text-slate-800 mt-0.5">{data.kpiLabel}</h3>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Valeur Réelle</p>
              <p className="text-xl font-extrabold text-blue-700 mt-0.5">
                {formatNumber(data.kpiValue)} <span className="text-xs font-semibold text-slate-500">{data.kpiUnit || ""}</span>
              </p>
            </div>
          </div>

          {/* Business-Friendly Source Description */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1">
              <Info className="h-4 w-4 text-blue-600" />
              Source des données (Vue Client)
            </h4>
            <div className="space-y-3 text-xs sm:text-sm">
              <div className="flex gap-2">
                <span className="font-bold text-slate-400 text-xs w-28 flex-shrink-0">Emplacement :</span>
                <span className="font-semibold text-slate-700">{translateOdooModel(data.model)}</span>
              </div>
              <div>
                <span className="font-bold text-slate-400 text-xs block mb-1">Critères de sélection appliqués :</span>
                <ul className="space-y-1.5 pl-4 list-disc text-slate-650 font-medium">
                  {businessFilters.map((filter, index) => (
                    <li key={index}>{filter}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Formula Rule */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1">
              <Settings className="h-4 w-4 text-blue-500" />
              Règle de Calcul & Logique Métier
            </h4>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs sm:text-sm text-slate-700 leading-relaxed font-semibold">
              {data.formula}
            </div>
          </div>

          {/* Evaluation / Threshold details if available */}
          {data.thresholdInfo && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1">
                <Activity className="h-4 w-4 text-amber-500" />
                Condition de Déclenchement de l'Alerte
              </h4>
              <div className="bg-amber-50/50 border border-amber-100 rounded-xl p-3 text-xs sm:text-sm text-slate-800 leading-relaxed font-semibold">
                {data.thresholdInfo}
              </div>
            </div>
          )}

          {/* Root Cause Analysis (Décomposition par segment & Résidu) */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1">
              <Activity className="h-4 w-4 text-rose-500" />
              Décomposition des causes racine (RCA)
            </h4>
            <RootCauseCard anomalyId={data.kpiId || data.anomalyId || ""} defaultExpanded={true} />

          </div>

          {/* History Details if Anomaly */}
          {data.historyValues && data.historyValues.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1">
                <Clock className="h-4 w-4 text-violet-500" />
                Historique & Analyse Statistique
              </h4>
              <div className="border border-slate-150 rounded-xl p-3 bg-slate-50/50 space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                  <div className="bg-white border border-slate-200 rounded-lg p-2.5 text-center">
                    <p className="text-[10px] text-slate-400 font-bold uppercase">Moyenne Historique</p>
                    <p className="text-sm font-extrabold text-slate-700 mt-1">
                      {formatNumber(data.mean || 0)}
                    </p>
                  </div>
                  <div className="bg-white border border-slate-200 rounded-lg p-2.5 text-center">
                    <p className="text-[10px] text-slate-400 font-bold uppercase">Z-Score Calculé</p>
                    <p className="text-sm font-extrabold text-violet-600 mt-1">
                      {data.zScore !== undefined ? (data.zScore > 0 ? `+${data.zScore.toFixed(2)}` : data.zScore.toFixed(2)) : "N/A"}
                    </p>
                  </div>
                  <div className="bg-white border border-slate-200 rounded-lg p-2.5 text-center col-span-2 sm:col-span-1">
                    <p className="text-[10px] text-slate-400 font-bold uppercase">Statut</p>
                    <p className="text-sm font-extrabold text-rose-600 mt-1 flex items-center justify-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-rose-600 animate-ping" />
                      Anomalie IA
                    </p>
                  </div>
                </div>

                <div className="text-xs">
                  <p className="text-[10px] text-slate-400 font-bold uppercase mb-2">Valeurs des 3 derniers mois (ordre chronologique)</p>
                  <div className="flex gap-2">
                    {data.historyValues.map((val, idx) => (
                      <div key={idx} className="flex-1 bg-white border border-slate-200 rounded-lg py-1.5 text-center font-mono font-bold text-slate-650">
                        {formatNumber(val)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Technical Collapsible View */}
          <div className="border-t border-slate-100 pt-4">
            <button
              onClick={() => setShowTechnical(!showTechnical)}
              className="w-full flex items-center justify-between text-xs font-bold text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
            >
              <span className="flex items-center gap-1">
                <FileCode className="h-4 w-4" />
                Détails techniques (Requête brute de l'API Odoo)
              </span>
              {showTechnical ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showTechnical && (
              <div className="mt-3 bg-slate-900 text-slate-200 rounded-xl p-3.5 font-mono text-[10px] sm:text-xs space-y-2 overflow-x-auto border border-slate-850 shadow-inner animate-slideDown">
                <div>
                  <span className="text-cyan-400">Modèle technique : </span>
                  <span className="text-amber-300">"{data.model}"</span>
                </div>
                <div className="pt-1.5 border-t border-slate-800">
                  <p className="text-emerald-400">Filtre technique (Domain Odoo) :</p>
                  <p className="text-slate-300 whitespace-pre-wrap mt-1 leading-relaxed bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    {data.domain}
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="bg-emerald-50/50 border border-emerald-100 rounded-xl p-3 flex gap-2.5 items-start">
            <CheckCircle className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed text-slate-600">
              <span className="font-bold text-emerald-800">Audit et traçabilité : </span>
              Ce rapport certifie la provenance des KPIs. Les valeurs proviennent du cache PostgreSQL synchronisé avec Odoo 17, éliminant tout risque d'hallucination de l'IA.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
