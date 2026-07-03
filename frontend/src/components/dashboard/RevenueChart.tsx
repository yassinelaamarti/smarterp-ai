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
      <div className="h-72 animate-pulse rounded-xl border border-gray-200 bg-gray-100" />
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Impossible de charger l&apos;historique du CA : {(error as Error)?.message ?? "erreur inconnue"}.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">
        Évolution du chiffre d&apos;affaires — 6 derniers mois
      </p>

      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0f6e56" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#0f6e56" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
              width={70}
              tickFormatter={(v) => v.toLocaleString("fr-FR")}
            />
            <Tooltip
              formatter={(value: number) => [formatMAD(value), "Chiffre d'affaires"]}
              contentStyle={{ borderRadius: 8, borderColor: "#e5e7eb", fontSize: 13 }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#0f6e56"
              strokeWidth={2}
              fill="url(#revenueFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
