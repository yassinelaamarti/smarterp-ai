"use client";

import { useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

export function ChatWindow() {
  const { messages, sendMessage, isSending, error } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();
  const prompt = searchParams.get("prompt");

  const hasSentRef = useRef(false);

  useEffect(() => {
    if (prompt && !hasSentRef.current) {
      hasSentRef.current = true;
      sendMessage(prompt);
      // Clean up the URL search params so reloading doesn't resend
      const newUrl = window.location.pathname;
      window.history.replaceState({}, "", newUrl);
    }
  }, [prompt, sendMessage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  return (
    <div className="flex h-[calc(100vh-12rem)] flex-col rounded-2xl border border-slate-200/80 bg-white shadow-sm">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-center">
            <div>
              <p className="text-sm font-semibold text-slate-700">
                Posez une question sur vos données
              </p>
              <p className="mt-1 text-xs text-slate-400 font-medium">
                Ex : « Pourquoi le chiffre d&apos;affaires a-t-il évolué ce mois-ci ? »
              </p>
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
