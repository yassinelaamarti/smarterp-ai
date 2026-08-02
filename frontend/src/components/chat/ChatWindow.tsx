"use client";

import { useRef, useEffect, useState } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useChat } from "@/hooks/useChat";
import { useConversations } from "@/hooks/useConversations";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { ConversationSidebar } from "./ConversationSidebar";
import { TrendingUp, Package, AlertTriangle, Users, Sparkles, ArrowRight, Download, Database, X, ChevronDown, ChevronUp } from "lucide-react";
import { cn, translateOdooModel, translateOdooDomain } from "@/lib/utils";
import { jsPDF } from "jspdf";
import { useKpis } from "@/hooks/useKpis";


const SUGGESTIONS = [
  {
    text: "Analyse l'évolution de notre chiffre d'affaires",
    label: "Performance financière",
    icon: TrendingUp,
    color: "text-emerald-600 bg-emerald-50 border-emerald-100",
  },
  {
    text: "Quels produits sont en rupture ou stock bas ?",
    label: "Gestion des stocks",
    icon: Package,
    color: "text-amber-600 bg-amber-50 border-amber-100",
  },
  {
    text: "Y a-t-il des commandes ou livraisons en retard ?",
    label: "Suivi des commandes",
    icon: AlertTriangle,
    color: "text-red-600 bg-red-50 border-red-100",
  },
  {
    text: "Quel est l'état du taux de conversion CRM ?",
    label: "Pipeline commercial",
    icon: Users,
    color: "text-purple-600 bg-purple-50 border-purple-100",
  },
];

export function ChatWindow() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const prompt = searchParams.get("prompt");
  const conversationIdParam = searchParams.get("conversation");
  const conversationId = conversationIdParam ? Number(conversationIdParam) : null;

  const { conversations, isLoading: conversationsLoading, createConversation } = useConversations();
  const { messages, sendMessage, isSending, error, conversationTitle } = useChat(conversationId);

  const bottomRef = useRef<HTMLDivElement>(null);
  const [showSources, setShowSources] = useState(false);
  const [expandedKpiIds, setExpandedKpiIds] = useState<{ [id: string]: boolean }>({});
  const { data: kpis } = useKpis();

  // --- Sélection automatique d'une conversation au premier chargement ---
  const hasInitializedRef = useRef(false);
  useEffect(() => {
    if (hasInitializedRef.current) return;
    if (prompt) return; // le flux "alerte" gère sa propre création
    if (conversationsLoading) return;
    if (conversationId !== null) {
      hasInitializedRef.current = true;
      return;
    }

    hasInitializedRef.current = true;
    if (conversations.length > 0) {
      router.replace(`${pathname}?conversation=${conversations[0].id}`);
    } else {
      createConversation().then((c) => {
        router.replace(`${pathname}?conversation=${c.id}`);
      });
    }
  }, [conversationId, conversations, conversationsLoading, prompt, pathname, router, createConversation]);

  // --- Flux "alerte -> question pré-remplie" (en 2 étapes) ---
  const hasCreatedForPromptRef = useRef(false);
  useEffect(() => {
    if (prompt && conversationId === null && !hasCreatedForPromptRef.current) {
      hasCreatedForPromptRef.current = true;
      createConversation().then((c) => {
        router.replace(`${pathname}?conversation=${c.id}&prompt=${encodeURIComponent(prompt)}`);
      });
    }
  }, [prompt, conversationId, pathname, router, createConversation]);

  const hasSentPromptRef = useRef(false);
  useEffect(() => {
    if (prompt && conversationId !== null && !hasSentPromptRef.current) {
      hasSentPromptRef.current = true;
      sendMessage(prompt);
      router.replace(`${pathname}?conversation=${conversationId}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prompt, conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const handleExportPDF = () => {
    const doc = new jsPDF({
      orientation: "portrait",
      unit: "mm",
      format: "a4",
    });

    const primaryColor = [113, 75, 103];
    const secondaryColor = [100, 116, 139];
    const textColor = [30, 41, 59];

    doc.setFillColor(primaryColor[0], primaryColor[1], primaryColor[2]);
    doc.rect(0, 0, 210, 30, "F");

    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.text("SmartERP AI", 15, 13);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.text("Rapport Décisionnel & Analyses de l'Agent IA", 15, 21);

    doc.setTextColor(textColor[0], textColor[1], textColor[2]);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.text("RAPPORT D'ANALYSE IA", 15, 42);

    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.5);
    doc.line(15, 45, 195, 45);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(secondaryColor[0], secondaryColor[1], secondaryColor[2]);
    const dateStr = new Date().toLocaleString("fr-FR", {
      dateStyle: "long",
      timeStyle: "short",
    });
    doc.text(`Généré le : ${dateStr}`, 15, 51);
    doc.text("Destinataire : Direction Générale / Management", 15, 56);
    doc.text("Source : Écosystème SmartERP AI & Odoo 17 Cache", 15, 61);
    if (conversationTitle) {
      doc.text(`Conversation : ${conversationTitle}`, 15, 66);
    }

    doc.line(15, 70, 195, 70);

    let yPosition = 80;

    messages.forEach((msg) => {
      if (yPosition > 270) {
        doc.addPage();
        yPosition = 20;
      }

      const isUser = msg.role === "user";

      doc.setFont("helvetica", "bold");
      doc.setFontSize(10);
      if (isUser) {
        doc.setTextColor(primaryColor[0], primaryColor[1], primaryColor[2]);
        doc.text("Question Utilisateur :", 15, yPosition);
      } else {
        doc.setTextColor(13, 148, 136);
        doc.text("Réponse de l'Assistant SmartERP AI :", 15, yPosition);
      }
      yPosition += 5.5;

      doc.setFont("helvetica", "normal");
      doc.setFontSize(9.5);
      doc.setTextColor(textColor[0], textColor[1], textColor[2]);

      const splitText = doc.splitTextToSize(msg.content, 180);
      splitText.forEach((line: string) => {
        if (yPosition > 278) {
          doc.addPage();
          yPosition = 20;
        }
        doc.text(line, 15, yPosition);
        yPosition += 5;
      });

      yPosition += 6.5;
    });

    const pageCount = doc.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(secondaryColor[0], secondaryColor[1], secondaryColor[2]);

      doc.setDrawColor(241, 245, 249);
      doc.setLineWidth(0.3);
      doc.line(15, 284, 195, 284);

      doc.text("SmartERP AI — Document Confidentiel à usage interne", 15, 289);
      doc.text(`Page ${i} sur ${pageCount}`, 180, 289);
    }

    doc.save(`SmartERP_AI_Rapport_${new Date().toISOString().slice(0, 10)}.pdf`);
  };

  return (
    <div className="flex h-[calc(100vh-12rem)] gap-4">
      <ConversationSidebar />

      <div className="flex flex-1 flex-col rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-3 bg-slate-50/50 rounded-t-2xl">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-semibold text-slate-500">
              {messages.length > 0 ? (conversationTitle ?? "Conversation active") : "Nouvelle conversation"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSources(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-slate-950 transition-colors shadow-2xs cursor-pointer"
            >
              <Database className="h-3.5 w-3.5 text-blue-500" />
              Données sources
            </button>
            {messages.length > 0 && (
              <button
                onClick={handleExportPDF}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-2xs cursor-pointer"
              >
                <Download className="h-3.5 w-3.5 text-slate-400" />
                Exporter en PDF
              </button>
            )}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center max-w-2xl mx-auto p-4 animate-fadeIn">
              <div className="relative mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25">
                <Sparkles className="h-5.5 w-5.5 animate-pulse" />
                <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 opacity-30 blur-xs -z-10 animate-ping" style={{ animationDuration: '3s' }} />
              </div>

              <h2 className="text-xl font-bold tracking-tight text-slate-800 sm:text-2xl">
                Assistant Virtuel SmartERP AI
              </h2>
              <p className="mt-2 text-xs sm:text-sm text-slate-500 font-medium max-w-md leading-relaxed">
                Posez vos questions métier en langage naturel ou commencez par l'une des suggestions ci-dessous :
              </p>


              <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
                {SUGGESTIONS.map((s, idx) => {
                  const Icon = s.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => sendMessage(s.text)}
                      className="group relative flex items-center gap-3.5 rounded-2xl border border-slate-250/70 bg-white p-4 text-left transition-all duration-300 hover:-translate-y-1 hover:border-blue-500 hover:shadow-md hover:shadow-blue-500/5 cursor-pointer"
                    >
                      <div className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-xl border flex-shrink-0 transition-transform duration-300 group-hover:scale-110",
                        s.color
                      )}>
                        <Icon className="h-4.5 w-4.5" />
                      </div>

                      <div className="flex-1 min-w-0 pr-6">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{s.label}</p>
                        <p className="text-xs sm:text-sm font-semibold text-slate-700 mt-0.5 truncate group-hover:text-blue-600 transition-colors duration-250">
                          {s.text}
                        </p>
                      </div>

                      <div className="absolute right-4 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-1 transition-all duration-300">
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <MessageBubble key={i} role={m.role} content={m.content} />
          ))}

          {isSending && <MessageBubble role="assistant" content="" isLoading />}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <ChatInput onSend={sendMessage} disabled={isSending || conversationId === null} />
      </div>

      {showSources && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
          <div className="relative flex flex-col w-full max-w-2xl max-h-[80vh] bg-white rounded-2xl border border-slate-200 shadow-2xl overflow-hidden animate-scaleIn">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
              <div className="flex items-center gap-2">
                <Database className="h-4.5 w-4.5 text-blue-600 animate-pulse" />
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-slate-800">Base de données source (KPIs)</h3>
                  <p className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase">Données transmises à l'agent IA</p>
                </div>
              </div>
              <button
                onClick={() => setShowSources(false)}
                className="p-1 rounded-lg hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
              <p className="text-[11px] leading-relaxed text-slate-650 bg-emerald-50 text-emerald-950 p-3 rounded-lg border border-emerald-100">
                ℹ️ <strong>Transparence de l'IA :</strong> Ces 10 indicateurs de performance sont injectés directement dans le contexte système de l'agent conversationnel pour chaque message. L'agent s'appuie exclusivement sur ces données auditées pour éviter toute hallucination.
              </p>
              
              <div className="grid grid-cols-1 gap-3">
                {kpis?.map((kpi) => {
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
                        <div className="mt-2 text-[10px] sm:text-xs text-slate-650 space-y-2">
                          <div className="flex gap-2">
                            <span className="font-bold text-slate-400 w-20 flex-shrink-0">Source :</span>
                            <span className="font-medium text-slate-700">{translateOdooModel(kpi.sourceData.model)}</span>
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
          </div>
        </div>
      )}
    </div>
  );
}
