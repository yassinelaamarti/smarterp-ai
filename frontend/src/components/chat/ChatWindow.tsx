"use client";

import { useRef, useEffect } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { TrendingUp, Package, AlertTriangle, Users } from "lucide-react";

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
          <div className="flex h-full flex-col items-center justify-center text-center max-w-xl mx-auto">
            <p className="text-sm font-semibold text-slate-700">
              Posez une question sur vos données
            </p>
            <p className="mt-1 text-xs text-slate-400 font-medium">
              Choisissez l&apos;une des suggestions ci-dessous ou saisissez votre message :
            </p>
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
              {SUGGESTIONS.map((s, idx) => {
                const Icon = s.icon;
                return (
                  <button
                    key={idx}
                    onClick={() => sendMessage(s.text)}
                    className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left hover:border-blue-500 hover:bg-blue-50/20 transition-all duration-200 cursor-pointer"
                  >
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg border flex-shrink-0 ${s.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-700">{s.label}</p>
                      <p className="text-[10px] text-slate-400 font-medium truncate mt-0.5 max-w-[200px]">
                        {s.text}
                      </p>
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
