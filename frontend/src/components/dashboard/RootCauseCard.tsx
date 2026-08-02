"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Layers, HelpCircle, Sparkles, TrendingDown, TrendingUp, Info } from "lucide-react";
import { useRootCause, RootCauseData } from "@/hooks/useRootCause";
import { cn } from "@/lib/utils";

interface RootCauseCardProps {
  anomalyId: string;
  defaultExpanded?: boolean;
}

const DIMENSION_LABELS: Record<string, string> = {
  region: "Région",
  product: "Produit",
  sales_rep: "Commercial",
  customer_category: "Client",
  customer: "Client",
};

export function RootCauseCard({ anomalyId, defaultExpanded = true }: RootCauseCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const { data: rca, isLoading, isError } = useRootCause(anomalyId);

  if (isLoading) {
    return (
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl animate-pulse flex items-center gap-2 text-xs text-slate-500 font-medium">
        <div className="h-4 w-4 rounded-full border-2 border-slate-300 border-t-indigo-600 animate-spin" />
        <span>Chargement de l'analyse des causes racines (RCA)...</span>
      </div>
    );
  }

  if (isError || !rca) {
    return (
      <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl flex items-start gap-2.5 text-xs text-slate-600">
        <Info className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-slate-700">Aucune anomalie statistique majeure détectée sur ce KPI</p>
          <p className="mt-0.5 text-[11px] text-slate-500 leading-relaxed">
            Cette alerte est déclenchée par une règle d'évaluation de seuil fixe (ex: stock disponible inférieur au seuil d'alerte ou retard de livraison) et ne nécessite pas de décomposition par segment.
          </p>
        </div>
      </div>
    );
  }


  const isDrop = rca.deltaTotalPct < 0;

  return (
    <div className="mt-3 border border-slate-200/80 rounded-xl bg-white/95 shadow-xs overflow-hidden transition-all">
      {/* Header dépliable */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-slate-50/70 hover:bg-slate-100/60 flex items-center justify-between transition-colors cursor-pointer text-left"
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800">
              Décomposition des causes racines (RCA)
            </span>
            <span className="ml-2 text-[10px] text-slate-400 font-semibold">
              Variation : {rca.deltaTotalPct > 0 ? `+${rca.deltaTotalPct}%` : `${rca.deltaTotalPct}%`}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
          <span>{isExpanded ? "Masquer" : "Voir le détail"}</span>
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {/* Contenu de la répartition */}
      {isExpanded && (
        <div className="p-4 space-y-4 border-t border-slate-100">
          {/* Explication LLM si présente */}
          {rca.explanation && (
            <div className="p-3 bg-indigo-50/60 border border-indigo-100 rounded-xl flex items-start gap-2.5">
              <Sparkles className="h-4 w-4 text-indigo-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs leading-relaxed text-indigo-950 font-medium">
                {rca.explanation}
              </p>
            </div>
          )}

          {/* Graphiques / Barres des facteurs principaux */}
          <div className="space-y-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Facteurs principaux (Top 3 par impact)
            </p>

            <div className="space-y-2.5">
              {rca.breakdown.map((item, index) => {
                const isItemPositive = item.delta > 0;
                const dimName = DIMENSION_LABELS[item.dimension] || item.dimension;
                const absContrib = Math.min(100, Math.abs(item.contributionPct));

                let cleanSegment = item.segment;
                const prefixes = ["Client : ", "Catégorie : ", "Étape : ", "Commercial : ", "Région : ", "Produit : "];
                for (const p of prefixes) {
                  if (cleanSegment.startsWith(p)) {
                    cleanSegment = cleanSegment.slice(p.length);
                    break;
                  }
                }

                return (
                  <div key={index} className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-slate-700 flex items-center gap-1.5">
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-medium">
                          {dimName}
                        </span>
                        {cleanSegment}
                      </span>

                      <span className={cn("font-bold font-mono text-xs", isItemPositive ? "text-emerald-600" : "text-rose-600")}>
                        {isItemPositive ? `+${item.delta}` : item.delta} ({item.contributionPct > 0 ? `+${item.contributionPct}%` : `${item.contributionPct}%`})
                      </span>
                    </div>

                    {/* Barre de progression proportionnelle */}
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden flex">
                      <div
                        className={cn("h-full transition-all duration-500 rounded-full", isItemPositive ? "bg-emerald-500" : "bg-rose-500")}
                        style={{ width: `${absContrib}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Affichage du résidu */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1">
              <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
              Part non expliquée (Résidu diffus) :
            </span>
            <span className={cn("font-bold font-mono", rca.residualPct > 40 ? "text-amber-600" : "text-slate-600")}>
              {rca.residualPct}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
