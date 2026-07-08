"use client";

import { useRef, useEffect } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { TrendingUp, Package, AlertTriangle, Users, Sparkles, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

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
  const { messages, sendMessage, isSending, error } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const prompt = searchParams.get("prompt");

  const hasSentRef = useRef(false);

  useEffect(() => {
    if (prompt && !hasSentRef.current) {
      hasSentRef.current = true;
      sendMessage(prompt);
      // Nettoie l'URL via le router Next (pas window.history directement,
      // pour que useSearchParams reste synchronisé correctement).
      router.replace(pathname, { scroll: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prompt]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  return (
    <div className="flex h-[calc(100vh-12rem)] flex-col rounded-2xl border border-slate-200/80 bg-white shadow-sm">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center max-w-2xl mx-auto p-4 animate-fadeIn">
            {/* Glowing Icon Container */}
            <div className="relative mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25">
              <Sparkles className="h-5.5 w-5.5 animate-pulse" />
              <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 opacity-30 blur-xs -z-10 animate-ping" style={{ animationDuration: '3s' }} />
            </div>

            <h2 className="text-xl font-bold tracking-tight text-slate-800 sm:text-2xl">
              Assistant Virtuel SmartERP AI
            </h2>
            <p className="mt-2 text-xs sm:text-sm text-slate-500 font-medium max-w-md leading-relaxed">
              Posez vos questions métier en langage naturel ou commencez par l&apos;une des suggestions ci-dessous :
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
                    {/* Icon with hover micro-animation */}
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

                    {/* Interactive indicator arrow */}
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

      <ChatInput onSend={sendMessage} disabled={isSending} />
    </div>
  );
}
