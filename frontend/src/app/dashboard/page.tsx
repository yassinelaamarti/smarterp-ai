"use client";

import React, { useState } from "react";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { RevenueChart } from "@/components/dashboard/RevenueChart";
import { AlertBanner } from "@/components/dashboard/AlertBanner";
import { AISummaryModal } from "@/components/dashboard/AISummaryModal";
import { HealthScoreCard } from "@/components/dashboard/HealthScoreCard";
import { RecommendationsList } from "@/components/dashboard/RecommendationsList";
import { Sparkles } from "lucide-react";

export default function DashboardPage() {
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Tableau de bord
          </h1>
          <p className="mt-1 text-sm text-slate-500 font-medium">
            Indicateurs clés synchronisés en temps réel avec Odoo 17
          </p>
        </div>

        <button
          onClick={() => setIsSummaryOpen(true)}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-500/10 hover:from-blue-500 hover:to-indigo-500 transition-all cursor-pointer self-start sm:self-auto"
        >
          <Sparkles className="h-4.5 w-4.5" />
          Synthèse IA
        </button>
      </div>

      <div className="mt-6">
        <HealthScoreCard />
      </div>

      <div className="mt-6 space-y-6">
        <AlertBanner />
        <RecommendationsList />
        <KPIGrid />
      </div>

      <div className="mt-8">
        <RevenueChart />
      </div>

      <AISummaryModal
        isOpen={isSummaryOpen}
        onClose={() => setIsSummaryOpen(false)}
      />
    </div>
  );
}

