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
      <div className="h-96 animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
    );
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
        Impossible de charger l&apos;historique du CA : {(error as Error)?.message ?? "erreur inconnue"}.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm hover:border-slate-300 transition-colors duration-300">
      <div className="mb-6">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
          Évolution du chiffre d&apos;affaires
        </h3>
        <p className="mt-1 text-xs text-slate-500 font-medium">
          Revenus consolidés mensuels sur les 6 derniers mois
        </p>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: "#64748b", fontWeight: 500 }}
              axisLine={{ stroke: "#e2e8f0" }}
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
                    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-lg">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{label}</p>
                      <p className="mt-1 text-sm font-bold text-slate-900">{formatMAD(val)}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#2563eb"
              strokeWidth={3}
              fill="url(#revenueFill)"
              activeDot={{ r: 6, stroke: "#2563eb", strokeWidth: 2, fill: "#ffffff" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
