"use client";

import { useHealthScore } from "@/hooks/useHealthScore";
import { cn } from "@/lib/utils";

function getScoreColors(score: number) {
  if (score >= 80) return { ring: "#10b981", text: "text-emerald-600" };
  if (score >= 60) return { ring: "#3b82f6", text: "text-blue-600" };
  if (score >= 40) return { ring: "#f59e0b", text: "text-amber-600" };
  return { ring: "#ef4444", text: "text-red-600" };
}

export function HealthScoreCard() {
  const { data, isLoading } = useHealthScore();

  if (isLoading || !data) {
    return (
      <div className="h-40 animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
    );
  }

  const colors = getScoreColors(data.score);
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (data.score / 100) * circumference;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-6">
        <div className="relative h-28 w-28 flex-shrink-0">
          <svg viewBox="0 0 100 100" className="h-28 w-28 -rotate-90">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" />
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke={colors.ring}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{ transition: "stroke-dashoffset 0.6s ease" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={cn("text-2xl font-bold", colors.text)}>{data.score}</span>
            <span className="text-[10px] text-slate-400">/ 100</span>
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Score de santé global
          </p>
          <p className={cn("mt-1 text-lg font-bold", colors.text)}>{data.label}</p>

          <ul className="mt-3 space-y-1.5">
            {data.factors.map((f, i) => {
              // Extraction optionnelle du tag entre crochets (ex: [Finance] ou [Opérations])
              const match = f.label.match(/^\[(.*?)\]\s*(.*)/);
              const catTag = match ? match[1] : null;
              const textContent = match ? match[2] : f.label;

              return (
                <li key={i} className="flex items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    {catTag && (
                      <span className="flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                        {catTag}
                      </span>
                    )}
                    <span className="text-slate-600 font-medium truncate" title={textContent}>
                      {textContent}
                    </span>
                  </div>
                  <span
                    className={cn(
                      "flex-shrink-0 font-bold font-mono text-[11px]",
                      f.impact > 0
                        ? "text-emerald-600"
                        : f.impact < 0
                        ? "text-red-600"
                        : "text-slate-400"
                    )}
                  >
                    {f.impact > 0 ? "+" : ""}
                    {f.impact} pts
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}
