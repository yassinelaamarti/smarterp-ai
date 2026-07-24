"use client";

import { useState } from "react";
import { useKpiHistory } from "@/hooks/useKpiHistory";
import { useKpiContext } from "@/hooks/useKpiContext";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { KPI } from "@/types";
import { 
  RevenueGoalWidget, 
  PipelineFunnelWidget, 
  StockAlertsWidget, 
  LateOrdersWidget,
  NewOrdersWidget,
  AvgOrderValueWidget,
  NewLeadsWidget,
  ConversionRateWidget,
  StockValueWidget,
  ActiveCustomersWidget
} from "./KPIContextWidgets";

interface KPIDetailModalProps {
  kpi: KPI;
  onClose: () => void;
}

type Period = "week" | "month" | "trimester";

export function KPIDetailModal({ kpi, onClose }: KPIDetailModalProps) {
  const [period, setPeriod] = useState<Period>("month");
  const { data: historyData, isLoading: historyLoading, isError: historyError } = useKpiHistory(kpi.id, period);
  const { data: contextData, isLoading: contextLoading } = useKpiContext(kpi.id, period);

  const formatValue = (value: number) => {
    return kpi.unit ? `${value.toLocaleString("fr-FR")} ${kpi.unit}` : value.toLocaleString("fr-FR");
  };

  const hasContext = contextData && contextData.type !== "none";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div className="w-full max-w-5xl bg-slate-50 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 bg-white">
          <div>
            <h2 className="text-xl font-bold text-slate-800 uppercase tracking-wide">
              {kpi.label}
            </h2>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-3xl font-black text-slate-900">
                {formatValue(kpi.value)}
              </span>
              {kpi.trend && kpi.trend !== "stable" && (
                <span
                  className={`px-2 py-1 text-xs font-bold rounded-md ${
                    kpi.trend === "up"
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {kpi.trend === "up" ? "+" : ""}
                  {kpi.changePercent}%
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 rounded-full transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 flex-1 overflow-y-auto">
          
          {/* Controls */}
          <div className="flex justify-end mb-4">
            <div className="inline-flex bg-white border border-slate-200 rounded-lg p-1 shadow-sm">
              <button
                onClick={() => setPeriod("week")}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  period === "week" ? "bg-slate-100 text-blue-700" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                7 Jours
              </button>
              <button
                onClick={() => setPeriod("month")}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  period === "month" ? "bg-slate-100 text-blue-700" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                30 Jours
              </button>
              <button
                onClick={() => setPeriod("trimester")}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  period === "trimester" ? "bg-slate-100 text-blue-700" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Trimestre
              </button>
            </div>
          </div>

          <div className={`grid gap-4 ${hasContext ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1'}`}>
            
            {/* Chart Area */}
            <div className={`bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-80 ${hasContext ? 'md:col-span-2' : ''}`}>
              {historyLoading ? (
                <div className="w-full h-full animate-pulse bg-slate-100 rounded-lg" />
              ) : historyError ? (
                <div className="w-full h-full flex items-center justify-center text-red-500 font-medium">
                  Erreur lors du chargement des données.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 11, fill: "#64748b", fontWeight: 500 }}
                      axisLine={{ stroke: "#e2e8f0" }}
                      tickLine={false}
                      dy={10}
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fill: "#64748b", fontWeight: 500 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v}
                      dx={-5}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-xl">
                              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                                {payload[0].payload.date}
                              </p>
                              <p className="text-sm font-bold text-slate-900 mt-1">
                                {formatValue(payload[0].value as number)}
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#3b82f6"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorValue)"
                      activeDot={{ r: 6, stroke: "#3b82f6", strokeWidth: 2, fill: "#ffffff" }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Context Widget Area */}
            {hasContext && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm h-80 overflow-hidden">
                {contextLoading ? (
                  <div className="w-full h-full animate-pulse bg-slate-100" />
                ) : (
                  <>
                    {contextData.type === 'goal' && <RevenueGoalWidget data={contextData.data} />}
                    {contextData.type === 'funnel' && <PipelineFunnelWidget data={contextData.data} />}
                    {contextData.type === 'table' && <StockAlertsWidget data={contextData.data} />}
                    {contextData.type === 'heatmap' && <LateOrdersWidget data={contextData.data} />}
                    {contextData.type === 'donut' && <NewOrdersWidget data={contextData.data} />}
                    {contextData.type === 'histogram' && <AvgOrderValueWidget data={contextData.data} />}
                    {contextData.type === 'radar' && <NewLeadsWidget data={contextData.data} />}
                    {contextData.type === 'win_loss' && <ConversionRateWidget data={contextData.data} />}
                    {contextData.type === 'aging' && <StockValueWidget data={contextData.data} />}
                    {contextData.type === 'leaderboard' && <ActiveCustomersWidget data={contextData.data} />}
                  </>
                )}
              </div>
            )}
            
          </div>
        </div>
      </div>
    </div>
  );
}
