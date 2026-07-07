import { Suspense } from "react";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function ChatPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Agent IA</h1>
      <p className="mt-1 text-sm text-slate-500">
        Posez vos questions en langage naturel sur vos données Odoo
      </p>

      <div className="mt-6">
        <Suspense fallback={
          <div className="flex h-[calc(100vh-12rem)] flex-col items-center justify-center rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
            <p className="text-sm text-slate-400 animate-pulse">Chargement de l'agent conversationnel...</p>
          </div>
        }>
          <ChatWindow />
        </Suspense>
      </div>
    </div>
  );
}

