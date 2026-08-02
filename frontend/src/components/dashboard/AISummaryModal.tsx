"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  X,
  Copy,
  Check,
  Download,
  MessageSquare,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Database,
  Info,
} from "lucide-react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { jsPDF } from "jspdf";
import { useKpis } from "@/hooks/useKpis";
import { translateOdooModel, translateOdooDomain } from "@/lib/utils";

interface AISummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AISummaryModal({ isOpen, onClose }: AISummaryModalProps) {
  const router = useRouter();
  const { data: kpis } = useKpis();
  const [summary, setSummary] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showSources, setShowSources] = useState<boolean>(false);
  const [expandedKpiIds, setExpandedKpiIds] = useState<{ [id: string]: boolean }>({});
  const modalRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    if (isOpen) {
      setShowSources(false);
      setExpandedKpiIds({});
      fetchSummary();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

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

  const fetchSummary = async () => {
    setIsLoading(true);
    setError(null);
    setSummary("");
    try {
      const response = await api.get<{ summary: string }>("/api/kpis/ai-summary");
      setSummary(response.data.summary);
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Impossible de générer le rapport. Veuillez vérifier que votre clé API Groq et votre serveur backend sont actifs."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text", err);
    }
  };

  const handleExportPDF = () => {
    if (!summary) return;
    const doc = new jsPDF({
      orientation: "portrait",
      unit: "mm",
      format: "a4",
    });

    const primaryColor = [30, 41, 59]; // slate-800
    const accentColor = [37, 99, 235]; // blue-600
    const textColor = [51, 65, 85]; // slate-700

    // Header Banner
    doc.setFillColor(37, 99, 235);
    doc.rect(0, 0, 210, 35, "F");

    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.text("SmartERP AI", 15, 14);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.text("Rapport de Synthèse Décisionnelle & Recommandations", 15, 22);
    doc.text("Instance : Odoo 17 Cache | Rapport IA Confidentiel", 15, 27);

    // Document Metadata
    doc.setTextColor(30, 41, 59);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.text("RAPPORT STRATÉGIQUE GLOBAL", 15, 48);

    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.5);
    doc.line(15, 51, 195, 51);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(100, 116, 139);
    const dateStr = new Date().toLocaleString("fr-FR", {
      dateStyle: "long",
      timeStyle: "short",
    });
    doc.text(`Généré le : ${dateStr}`, 15, 57);
    doc.text("Destinataire : Direction Générale / Direction Commerciale", 15, 62);

    doc.line(15, 66, 195, 66);

    let yPosition = 75;
    const lines = summary.split("\n");

    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.setTextColor(textColor[0], textColor[1], textColor[2]);

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        yPosition += 4;
        return;
      }

      const splitText = doc.splitTextToSize(trimmed, 180);
      splitText.forEach((pLine: string) => {
        if (yPosition > 270) {
          doc.addPage();
          yPosition = 20;
        }

        if (pLine.startsWith("##") || pLine.startsWith("#")) {
          yPosition += 4;
          doc.setFont("helvetica", "bold");
          doc.setFontSize(11);
          doc.setTextColor(accentColor[0], accentColor[1], accentColor[2]);
          doc.text(pLine.replace(/#+\s+/, ""), 15, yPosition);
          doc.setFont("helvetica", "normal");
          doc.setFontSize(10);
          doc.setTextColor(textColor[0], textColor[1], textColor[2]);
          yPosition += 6;
        } else if (pLine.startsWith("- ") || pLine.startsWith("* ")) {
          doc.setFont("helvetica", "normal");
          doc.text("• " + pLine.substring(2), 20, yPosition);
          yPosition += 5.5;
        } else if (/^\d+\.\s+/.test(pLine)) {
          doc.setFont("helvetica", "bold");
          doc.text(pLine, 15, yPosition);
          doc.setFont("helvetica", "normal");
          yPosition += 5.5;
        } else {
          // Check for bold text chunks
          if (pLine.includes("**")) {
            // Simple split for bold parts
            const parts = pLine.split("**");
            let xOffset = 15;
            parts.forEach((part, idx) => {
              const isBold = idx % 2 !== 0;
              doc.setFont("helvetica", isBold ? "bold" : "normal");
              if (isBold) doc.setTextColor(30, 41, 59);
              else doc.setTextColor(textColor[0], textColor[1], textColor[2]);
              
              doc.text(part, xOffset, yPosition);
              xOffset += doc.getTextWidth(part);
            });
            yPosition += 5.5;
          } else {
            doc.text(pLine, 15, yPosition);
            yPosition += 5.5;
          }
        }
      });
    });

    // Add footer on all pages
    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(148, 163, 184);
      doc.line(15, 282, 195, 282);
      doc.text("SmartERP AI — Rapport Stratégique Confidentiel", 15, 287);
      doc.text(`Page ${i} sur ${pageCount}`, 180, 287);
    }

    doc.save(`SmartERP_AI_Synthese_${new Date().toISOString().slice(0, 10)}.pdf`);
  };

  const handleDiscussInChat = () => {
    const promptText = `Concernant le rapport de synthèse décisionnelle de notre tableau de bord que tu as rédigé, je souhaite approfondir l'analyse et obtenir d'autres conseils opérationnels spécifiques.`;
    router.push(`/dashboard/chat?prompt=${encodeURIComponent(promptText)}`);
    onClose();
  };

  const renderBoldText = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={index} className="font-bold text-slate-800">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });
  };

  const parseMarkdownToReact = (text: string) => {
    if (!text) return null;
    return text.split("\n").map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} className="h-3" />;

      if (trimmed.startsWith("### ")) {
        return (
          <h4 key={idx} className="mt-4 mb-2 text-sm font-bold text-slate-800">
            {trimmed.replace("### ", "")}
          </h4>
        );
      }

      if (trimmed.startsWith("## ") || trimmed.startsWith("# ")) {
        const title = trimmed.replace(/^#+\s+/, "");
        return (
          <h3
            key={idx}
            className="mt-6 mb-3 text-sm sm:text-base font-bold text-blue-900 border-b border-slate-100 pb-2 flex items-center gap-2"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
            {title}
          </h3>
        );
      }

      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        const content = trimmed.substring(2);
        return (
          <li
            key={idx}
            className="ml-5 list-disc text-xs sm:text-sm text-slate-600 mb-1.5 leading-relaxed"
          >
            {renderBoldText(content)}
          </li>
        );
      }

      if (/^\d+\.\s+/.test(trimmed)) {
        const content = trimmed.replace(/^\d+\.\s+/, "");
        return (
          <div key={idx} className="flex gap-2.5 items-start mt-4 mb-3">
            <span className="flex-shrink-0 flex items-center justify-center h-5 w-5 rounded-full bg-blue-50 text-blue-600 text-xs font-bold font-mono">
              {trimmed.match(/^\d+/)?.[0]}
            </span>
            <div className="text-xs sm:text-sm font-semibold text-slate-700 flex-1 leading-relaxed">
              {renderBoldText(content)}
            </div>
          </div>
        );
      }

      return (
        <p key={idx} className="text-xs sm:text-sm text-slate-600 leading-relaxed mb-3">
          {renderBoldText(trimmed)}
        </p>
      );
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div
        ref={modalRef}
        className="relative flex flex-col w-full max-w-3xl max-h-[85vh] bg-white rounded-2xl border border-slate-200 shadow-2xl overflow-hidden transition-all scale-100"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Sparkles className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-slate-800">
                Synthèse Décisionnelle IA
              </h2>
              <p className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase">
                Rapport stratégique en temps réel
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
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="relative">
                <RefreshCw className="h-10 w-10 text-blue-600 animate-spin" />
                <Sparkles className="absolute -top-1 -right-1 h-4 w-4 text-amber-500 animate-pulse" />
              </div>
              <div className="text-center">
                <p className="text-sm font-bold text-slate-700">Génération de la synthèse en cours...</p>
                <p className="text-xs text-slate-400 font-medium mt-1">
                  L'agent IA étudie l'évolution du CA, de la logistique et de votre CRM...
                </p>
              </div>
              
              {/* Skeleton loading preview bars */}
              <div className="w-full max-w-md space-y-3 mt-6">
                <div className="h-4 bg-slate-100 rounded-md w-3/4 animate-pulse" />
                <div className="h-3 bg-slate-100 rounded-md w-full animate-pulse" />
                <div className="h-3 bg-slate-100 rounded-md w-5/6 animate-pulse" />
                <div className="h-4 bg-slate-100 rounded-md w-1/2 animate-pulse mt-4" />
                <div className="h-3 bg-slate-100 rounded-md w-full animate-pulse" />
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-xs sm:text-sm text-red-700 flex flex-col gap-2 items-center text-center">
              <p className="font-semibold">{error}</p>
              <button
                onClick={fetchSummary}
                className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-red-200 text-red-700 text-xs font-semibold hover:bg-red-50 cursor-pointer"
              >
                <RefreshCw className="h-3 w-3" />
                Réessayer
              </button>
            </div>
          )}

          {!isLoading && !error && summary && (
            <>
              <div className="prose prose-slate max-w-none">
                {parseMarkdownToReact(summary)}
              </div>

              {/* Collapsible Source Data Section */}
              <div className="mt-8 pt-6 border-t border-slate-150">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900 hover:border-slate-300 transition-all font-semibold text-xs sm:text-sm cursor-pointer shadow-2xs"
                >
                  <span className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-blue-600 animate-pulse" />
                    <span>Explicabilité IA : Voir les données sources ({kpis?.length || 0} KPIs audités)</span>
                  </span>
                  {showSources ? (
                    <ChevronUp className="h-4 w-4 text-slate-500" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-500" />
                  )}
                </button>

                {showSources && kpis && (
                  <div className="mt-4 space-y-4 animate-slideDown">
                    <p className="text-[11px] text-slate-500 font-medium leading-relaxed bg-emerald-50 text-emerald-950 p-3 rounded-lg border border-emerald-100">
                      ℹ️ <strong>Rapport Audité :</strong> Les chiffres analysés par l'IA ci-dessus proviennent des requêtes directes configurées sur Odoo 17 et stockées en cache PostgreSQL.
                    </p>
                    <div className="grid grid-cols-1 gap-3">
                      {kpis.map((kpi) => {
                        const isTechExpanded = !!expandedKpiIds[kpi.id];
                        return (
                          <div key={kpi.id} className="border border-slate-200 rounded-xl p-3 bg-white hover:border-slate-350 transition-all">
                            <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                              <span className="font-bold text-xs text-slate-800">{kpi.label}</span>
                              <span className="font-mono text-xs font-bold text-blue-600">
                                {new Intl.NumberFormat("fr-FR").format(kpi.value)} {kpi.unit || ""}
                              </span>
                            </div>
                            {kpi.sourceData && (
                              <div className="mt-2 text-[10px] sm:text-xs text-slate-600 space-y-2">
                                <div className="flex gap-2">
                                  <span className="font-bold text-slate-400 w-20 flex-shrink-0">Source :</span>
                                  <span className="font-semibold text-slate-700">{translateOdooModel(kpi.sourceData.model)}</span>
                                </div>
                                <div className="flex gap-2">
                                  <span className="font-bold text-slate-400 w-20 flex-shrink-0">Sélection :</span>
                                  <div className="font-medium text-slate-700">
                                    <ul className="list-disc pl-4 space-y-0.5">
                                      {translateOdooDomain(kpi.sourceData.domain).map((f, i) => (
                                        <li key={i}>{f}</li>
                                      ))}
                                    </ul>
                                  </div>
                                </div>
                                <div className="flex gap-2 pb-1">
                                  <span className="font-bold text-slate-400 w-20 flex-shrink-0">Règle :</span>
                                  <span className="font-semibold text-slate-700">{kpi.sourceData.formula}</span>
                                </div>
                                
                                <div className="border-t border-slate-100 pt-2">
                                  <button
                                    onClick={() => setExpandedKpiIds((prev) => ({ ...prev, [kpi.id]: !prev[kpi.id] }))}
                                    className="flex items-center justify-between w-full text-[9px] sm:text-[10px] font-bold text-slate-450 hover:text-slate-600 transition-colors cursor-pointer"
                                  >
                                    <span>Requête technique Odoo</span>
                                    {isTechExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                                  </button>
                                  {isTechExpanded && (
                                    <div className="mt-1.5 bg-slate-900 text-slate-200 p-2 rounded-lg font-mono text-[9px] sm:text-[10px] space-y-1 overflow-x-auto border border-slate-800 shadow-inner">
                                      <div><span className="text-cyan-400">Modèle :</span> "{kpi.sourceData.model}"</div>
                                      <div><span className="text-emerald-400">Filtre :</span> {kpi.sourceData.domain}</div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        {!isLoading && !error && summary && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-6 py-4 border-t border-slate-150 bg-slate-50/50">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                onClick={handleCopy}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer"
                title="Copier dans le presse-papiers"
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 text-emerald-600" />
                    <span className="text-emerald-700">Copié !</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 text-slate-400" />
                    <span>Copier le rapport</span>
                  </>
                )}
              </button>

              <button
                onClick={handleExportPDF}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer"
              >
                <Download className="h-4 w-4 text-slate-400" />
                <span>Exporter en PDF</span>
              </button>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <button
                onClick={handleDiscussInChat}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-blue-500/10 hover:from-blue-500 hover:to-indigo-500 transition-all cursor-pointer"
              >
                <MessageSquare className="h-4 w-4" />
                <span>Discuter avec l'IA</span>

              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
