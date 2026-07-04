"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useRevenueHistory } from "@/hooks/useRevenueHistory";

function formatMAD(value: number) {
  return `${value.toLocaleString("fr-FR")} MAD`;
}

export function RevenueChart() {
  const { data, isLoading, isError, error } = useRevenueHistory(6);

  if (isLoading) {
    return (
      <div className="h-96 animate-pulse rounded-2xl border border-slate-900 bg-slate-900/20" />
    );
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-red-900/20 bg-red-950/20 p-5 text-sm text-red-400 backdrop-blur-xl">
        Impossible de charger l&apos;historique du CA : {(error as Error)?.message ?? "erreur inconnue"}.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-900 bg-slate-900/40 p-6 backdrop-blur-xl shadow-sm hover:border-slate-800 transition-colors duration-300">
      <div className="mb-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Évolution du chiffre d&apos;affaires
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          Revenus consolidés mensuels sur les 6 derniers mois
        </p>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: "#64748b", fontWeight: 500 }}
              axisLine={{ stroke: "#1e293b" }}
              tickLine={false}
              dy={10}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#64748b", fontWeight: 500 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
              dx={-5}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const val = payload[0].value as number;
                  const label = payload[0].payload.label;
                  return (
                    <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 shadow-xl backdrop-blur-xl">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</p>
                      <p className="mt-1 text-sm font-bold text-white">{formatMAD(val)}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#6366f1"
              strokeWidth={3}
              fill="url(#revenueFill)"
              activeDot={{ r: 6, stroke: "#6366f1", strokeWidth: 2, fill: "#0f172a" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
