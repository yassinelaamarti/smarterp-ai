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
  ShieldCheck,
  TrendingUp,
  Package,
  AlertTriangle,
  Calendar,
  Clock,
  Building2,
  UserCheck,
  CheckCircle2,
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
          "Impossible de générer le rapport. Veuillez vérifier votre connexion au serveur backend."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      // Nettoyer les astérisques bruts et balises pour la copie texte propre
      const cleanText = summary
        .replace(/\*\*(.*?)\*\*/g, "$1")
        .replace(/^#+\s+/gm, "")
        .trim();

      const headerText = `SMARTERP AI — RAPPORT STRATÉGIQUE D'ENTREPRISE\nDate : ${new Date().toLocaleDateString("fr-FR")} | Période analysée : 30 derniers jours\nDestinataire : Direction Générale / Board\n--------------------------------------------------\n\n`;

      await navigator.clipboard.writeText(headerText + cleanText);
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
    doc.setFillColor(30, 41, 59);
    doc.rect(0, 0, 210, 36, "F");

    // Decorative Accent Line
    doc.setFillColor(37, 99, 235);
    doc.rect(0, 35, 210, 2, "F");

    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(20);
    doc.text("SmartERP AI", 15, 14);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.text("RAPPORT DE SYNTHÈSE DÉCISIONNELLE STRATÉGIQUE", 15, 22);
    doc.setFontSize(8.5);
    doc.setTextColor(203, 213, 225);
    doc.text("Instance Odoo 17 PostgreSQL Cache | Document Confidentiel - Usage Direction", 15, 28);

    // Document Metadata Block
    doc.setFillColor(248, 250, 252);
    doc.rect(15, 42, 180, 24, "F");
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.4);
    doc.rect(15, 42, 180, 24, "S");

    doc.setTextColor(30, 41, 59);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text("MÉTADONNÉES DU RAPPORT EXÉCUTIF", 20, 48);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.5);
    doc.setTextColor(100, 116, 139);

    const dateStr = new Date().toLocaleString("fr-FR", {
      dateStyle: "long",
      timeStyle: "short",
    });
    doc.text(`• Date de génération : ${dateStr}`, 20, 54);
    doc.text("• Période analysée : 30 derniers jours", 20, 60);
    doc.text("• Destinataires : Direction Générale / Comité de Direction", 105, 54);
    doc.text("• Statut : Rapport d'Audit & Recommandations IA", 105, 60);

    let yPosition = 75;
    const lines = summary.split("\n");

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9.5);
    doc.setTextColor(textColor[0], textColor[1], textColor[2]);

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        yPosition += 3.5;
        return;
      }

      // Nettoyer la ligne pour mesurer/traiter
      const splitText = doc.splitTextToSize(trimmed, 180);
      splitText.forEach((pLine: string) => {
        if (yPosition > 270) {
          doc.addPage();
          yPosition = 20;
        }

        if (pLine.startsWith("## ") || pLine.startsWith("# ")) {
          yPosition += 4;
          const cleanHeading = pLine.replace(/^#+\s+/, "").replace(/\*\*/g, "");
          doc.setFillColor(241, 245, 249);
          doc.rect(15, yPosition - 4, 180, 7, "F");
          doc.setFont("helvetica", "bold");
          doc.setFontSize(11);
          doc.setTextColor(30, 41, 59);
          doc.text(cleanHeading, 18, yPosition + 1);
          doc.setFont("helvetica", "normal");
          doc.setFontSize(9.5);
          doc.setTextColor(textColor[0], textColor[1], textColor[2]);
          yPosition += 8;
        } else if (pLine.startsWith("### ")) {
          yPosition += 3;
          const cleanSub = pLine.replace("### ", "").replace(/\*\*/g, "");
          doc.setFont("helvetica", "bold");
          doc.setFontSize(10);
          doc.setTextColor(37, 99, 235);
          doc.text("• " + cleanSub, 15, yPosition);
          doc.setFont("helvetica", "normal");
          doc.setFontSize(9.5);
          doc.setTextColor(textColor[0], textColor[1], textColor[2]);
          yPosition += 6;
        } else if (pLine.startsWith("- ") || pLine.startsWith("* ")) {
          const cleanBullet = pLine.substring(2);
          doc.setFont("helvetica", "normal");
          doc.text("  - ", 15, yPosition);

          // Render inline bold text without raw asterisks
          renderPdfFormattedLine(doc, cleanBullet, 22, yPosition, textColor);
          yPosition += 5.5;
        } else if (/^\d+\.\s+/.test(pLine)) {
          doc.setFont("helvetica", "bold");
          const numMatch = pLine.match(/^(\d+\.)\s+(.*)/);
          if (numMatch) {
            doc.setTextColor(37, 99, 235);
            doc.text(numMatch[1], 15, yPosition);
            renderPdfFormattedLine(doc, numMatch[2], 23, yPosition, textColor);
          } else {
            renderPdfFormattedLine(doc, pLine, 15, yPosition, textColor);
          }
          yPosition += 5.5;
        } else {
          renderPdfFormattedLine(doc, pLine, 15, yPosition, textColor);
          yPosition += 5.5;
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
      doc.text("SmartERP AI — Rapport Stratégique Confidentiel (Odoo 17 Cache)", 15, 287);
      doc.text(`Page ${i} sur ${pageCount}`, 180, 287);
    }

    doc.save(`SmartERP_AI_Synthese_Executive_${new Date().toISOString().slice(0, 10)}.pdf`);
  };

  const renderPdfFormattedLine = (
    doc: jsPDF,
    text: string,
    xStart: number,
    yPos: number,
    defaultColor: number[]
  ) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    let xOffset = xStart;

    parts.forEach((part) => {
      if (!part) return;
      const isBold = part.startsWith("**") && part.endsWith("**");
      const cleanContent = isBold ? part.slice(2, -2) : part;

      doc.setFont("helvetica", isBold ? "bold" : "normal");
      if (isBold) {
        doc.setTextColor(30, 41, 59);
      } else {
        doc.setTextColor(defaultColor[0], defaultColor[1], defaultColor[2]);
      }

      doc.text(cleanContent, xOffset, yPos);
      xOffset += doc.getTextWidth(cleanContent);
    });
  };

  const handleDiscussInChat = () => {
    const promptText = `Concernant le rapport de synthèse décisionnelle de notre tableau de bord que tu as rédigé, je souhaite approfondir l'analyse et obtenir d'autres conseils opérationnels spécifiques.`;
    router.push(`/dashboard/chat?prompt=${encodeURIComponent(promptText)}`);
    onClose();
  };

  /**
   * Rendu intelligent des balises en gras (**text**) sous forme de badges / pills colorés
   * pour mettre visuellement en valeur les chiffres clés (CA, %, points, scores).
   */
  const renderExecutiveText = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        const val = part.slice(2, -2);

        // Détection de la polarité pour le code couleur
        const isPositive =
          val.includes("+") ||
          val.toLowerCase().includes("hausse") ||
          val.toLowerCase().includes("progression") ||
          val.toLowerCase().includes("excellente") ||
          val.toLowerCase().includes("préservé");

        const isNegative =
          val.includes("-") ||
          val.toLowerCase().includes("baisse") ||
          val.toLowerCase().includes("retard") ||
          val.toLowerCase().includes("critique") ||
          val.toLowerCase().includes("rupture") ||
          val.toLowerCase().includes("chute");

        const isScore = val.includes("/100");

        if (isPositive) {
          return (
            <span
              key={index}
              className="inline-flex items-center px-2 py-0.5 my-0.5 mx-0.5 rounded-md text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200/80 shadow-2xs"
            >
              {val}
            </span>
          );
        } else if (isNegative) {
          return (
            <span
              key={index}
              className="inline-flex items-center px-2 py-0.5 my-0.5 mx-0.5 rounded-md text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200/80 shadow-2xs"
            >
              {val}
            </span>
          );
        } else if (isScore) {
          return (
            <span
              key={index}
              className="inline-flex items-center px-2.5 py-0.5 my-0.5 mx-0.5 rounded-lg text-xs font-extrabold bg-blue-600 text-white shadow-sm"
            >
              {val}
            </span>
          );
        } else {
          return (
            <span
              key={index}
              className="inline-flex items-center px-1.5 py-0.5 my-0.5 mx-0.5 rounded text-xs font-bold bg-slate-100 text-slate-800 border border-slate-200/80"
            >
              {val}
            </span>
          );
        }
      }
      return part;
    });
  };

  /**
   * Rendu Markdown professionnel structuré par sections exécutives.
   */
  const renderExecutiveReport = (text: string) => {
    if (!text) return null;

    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];

    lines.forEach((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) {
        elements.push(<div key={`sp-${idx}`} className="h-2" />);
        return;
      }

      // Section H2 principaux (ex: ## 1. Synthèse Exécutive...)
      if (trimmed.startsWith("## ")) {
        const title = trimmed.replace("## ", "").replace(/\*\*/g, "");
        elements.push(
          <div key={`h2-${idx}`} className="mt-7 mb-4">
            <div className="flex items-center gap-2.5 border-b border-slate-200 pb-2.5">
              <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-600 text-white text-xs font-bold shadow-xs">
                {title.match(/^\d+/)?.[0] || "•"}
              </span>
              <h3 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
                {title.replace(/^\d+\.\s*/, "")}
              </h3>
            </div>
          </div>
        );
        return;
      }

      // Sous-titres H3 (ex: ### Performance Financière...)
      if (trimmed.startsWith("### ")) {
        const subtitle = trimmed.replace("### ", "").replace(/\*\*/g, "");
        elements.push(
          <div key={`h3-${idx}`} className="mt-5 mb-2.5 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-blue-500" />
            <h4 className="text-xs sm:text-sm font-bold text-slate-800 uppercase tracking-wide">
              {subtitle}
            </h4>
          </div>
        );
        return;
      }

      // Puces de liste (- ou *)
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        const content = trimmed.substring(2);
        elements.push(
          <div key={`li-${idx}`} className="flex items-start gap-2 ml-2 mb-2">
            <span className="text-blue-500 font-bold text-xs mt-0.5">•</span>
            <div className="text-xs sm:text-sm text-slate-700 leading-relaxed flex-1">
              {renderExecutiveText(content)}
            </div>
          </div>
        );
        return;
      }

      // Listes numérotées (1., 2., 3.) pour le plan d'actions
      if (/^\d+\.\s+/.test(trimmed)) {
        const num = trimmed.match(/^\d+/)?.[0];
        const content = trimmed.replace(/^\d+\.\s+/, "");
        elements.push(
          <div
            key={`num-${idx}`}
            className="flex items-start gap-3 p-3.5 my-2.5 rounded-xl border border-blue-100 bg-blue-50/40 hover:bg-blue-50/70 transition-colors"
          >
            <span className="flex-shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white font-mono text-xs font-bold shadow-2xs">
              {num}
            </span>
            <div className="text-xs sm:text-sm text-slate-800 font-medium leading-relaxed flex-1 pt-0.5">
              {renderExecutiveText(content)}
            </div>
          </div>
        );
        return;
      }

      // Paragraphes normaux
      elements.push(
        <p key={`p-${idx}`} className="text-xs sm:text-sm text-slate-700 leading-relaxed mb-3">
          {renderExecutiveText(trimmed)}
        </p>
      );
    });

    return elements;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div
        ref={modalRef}
        className="relative flex flex-col w-full max-w-4xl max-h-[90vh] bg-white rounded-2xl border border-slate-200 shadow-2xl overflow-hidden transition-all scale-100"
      >
        {/* Header Institutionnel */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-150 bg-slate-900 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-bold tracking-tight">
                  Synthèse Décisionnelle IA
                </h2>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30">
                  <ShieldCheck className="h-3 w-3" /> Rapport Board
                </span>
              </div>
              <p className="text-[11px] text-slate-300 font-medium mt-0.5">
                Audit de performance & recommandations stratégiques en temps réel
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin space-y-6">
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <div className="relative">
                <RefreshCw className="h-10 w-10 text-blue-600 animate-spin" />
                <Sparkles className="absolute -top-1 -right-1 h-4 w-4 text-amber-500 animate-pulse" />
              </div>
              <div className="text-center">
                <p className="text-sm font-bold text-slate-800">Génération du rapport exécutif en cours...</p>
                <p className="text-xs text-slate-500 font-medium mt-1">
                  L'agent IA analyse le CA, la conversion CRM, la logistique et le score de santé global...
                </p>
              </div>

              {/* Skeleton loading preview bars */}
              <div className="w-full max-w-lg space-y-3 mt-6">
                <div className="h-5 bg-slate-100 rounded-md w-3/4 animate-pulse" />
                <div className="h-3.5 bg-slate-100 rounded-md w-full animate-pulse" />
                <div className="h-3.5 bg-slate-100 rounded-md w-5/6 animate-pulse" />
                <div className="h-5 bg-slate-100 rounded-md w-1/2 animate-pulse mt-4" />
                <div className="h-3.5 bg-slate-100 rounded-md w-full animate-pulse" />
              </div>
            </div>
          )}

          {error && (
            <div className="p-5 rounded-2xl border border-red-200 bg-red-50 text-xs sm:text-sm text-red-700 flex flex-col gap-2 items-center text-center">
              <p className="font-bold">{error}</p>
              <button
                onClick={fetchSummary}
                className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white border border-red-200 text-red-700 text-xs font-bold hover:bg-red-50 cursor-pointer shadow-2xs"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Réessayer la génération
              </button>
            </div>
          )}

          {!isLoading && !error && summary && (
            <>
              {/* Entête du Document Executive / Board */}
              <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 shadow-2xs">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-blue-600 flex-shrink-0" />
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Généré le</p>
                      <p className="font-semibold text-slate-800">
                        {new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Période analysée</p>
                      <p className="font-semibold text-slate-800">30 derniers jours</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-purple-600 flex-shrink-0" />
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Source de données</p>
                      <p className="font-semibold text-slate-800">Odoo 17 Cache</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <UserCheck className="h-4 w-4 text-amber-600 flex-shrink-0" />
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Destinataire</p>
                      <p className="font-semibold text-slate-800">Direction Générale</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Rendu Markdown Professionnel */}
              <div className="prose prose-slate max-w-none">
                {renderExecutiveReport(summary)}
              </div>

              {/* Collapsible Source Data Section */}
              <div className="mt-8 pt-6 border-t border-slate-150">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="w-full flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-all font-semibold text-xs sm:text-sm cursor-pointer shadow-2xs"
                >
                  <span className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-blue-600" />
                    <span>Explicabilité IA : Voir les {kpis?.length || 0} indicateurs audités</span>
                  </span>
                  {showSources ? (
                    <ChevronUp className="h-4 w-4 text-slate-500" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-500" />
                  )}
                </button>

                {showSources && kpis && (
                  <div className="mt-4 space-y-3 animate-slideDown">
                    <p className="text-[11px] text-slate-600 font-medium leading-relaxed bg-emerald-50 text-emerald-950 p-3 rounded-xl border border-emerald-200/60">
                      ℹ️ <strong>Transparence & Traçabilité :</strong> Ce rapport s'appuie exclusivement sur les requêtes configurées sur Odoo 17 et stockées dans le cache PostgreSQL de SmartERP AI.
                    </p>
                    <div className="grid grid-cols-1 gap-2.5">
                      {kpis.map((kpi) => {
                        const isTechExpanded = !!expandedKpiIds[kpi.id];
                        return (
                          <div key={kpi.id} className="border border-slate-200 rounded-xl p-3 bg-white hover:border-slate-300 transition-all">
                            <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                              <span className="font-bold text-xs text-slate-800">{kpi.label}</span>
                              <span className="font-mono text-xs font-bold text-blue-600">
                                {new Intl.NumberFormat("fr-FR").format(kpi.value)} {kpi.unit || ""}
                              </span>
                            </div>
                            {kpi.sourceData && (
                              <div className="mt-2 text-[10px] sm:text-xs text-slate-600 space-y-1.5">
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
                                    className="flex items-center justify-between w-full text-[9px] sm:text-[10px] font-bold text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                                  >
                                    <span>Requête technique Odoo</span>
                                    {isTechExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                                  </button>
                                  {isTechExpanded && (
                                    <div className="mt-1.5 bg-slate-900 text-slate-200 p-2.5 rounded-lg font-mono text-[9px] sm:text-[10px] space-y-1 overflow-x-auto border border-slate-800 shadow-inner">
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
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-6 py-4 border-t border-slate-150 bg-slate-50">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                onClick={handleCopy}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 rounded-xl border border-slate-250 bg-white px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-100 transition-colors shadow-2xs cursor-pointer"
                title="Copier le rapport nettoyé"
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 text-emerald-600" />
                    <span className="text-emerald-700">Rapport copié !</span>
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
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 rounded-xl border border-slate-250 bg-white px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-100 transition-colors shadow-2xs cursor-pointer"
              >
                <Download className="h-4 w-4 text-slate-400" />
                <span>Exporter en PDF</span>
              </button>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <button
                onClick={handleDiscussInChat}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/20 hover:from-blue-500 hover:to-indigo-500 transition-all cursor-pointer"
              >
                <MessageSquare className="h-4 w-4" />
                <span>Discuter des recommandations</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
