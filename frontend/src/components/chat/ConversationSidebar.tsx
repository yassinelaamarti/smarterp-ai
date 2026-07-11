"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useConversations } from "@/hooks/useConversations";

function formatRelativeTime(iso: string): string {
  const diffMin = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (diffMin < 1) return "À l'instant";
  if (diffMin < 60) return `Il y a ${diffMin} min`;
  const diffH = Math.round(diffMin / 60);
  if (diffH < 24) return `Il y a ${diffH} h`;
  return `Il y a ${Math.round(diffH / 24)} j`;
}

export function ConversationSidebar() {
  const { conversations, isLoading, createConversation, deleteConversation } = useConversations();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeId = searchParams.get("conversation");

  async function handleCreate() {
    const conversation = await createConversation();
    router.push(`${pathname}?conversation=${conversation.id}`);
  }

  function handleSelect(id: number) {
    router.push(`${pathname}?conversation=${id}`);
  }

  function handleDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation();
    deleteConversation(id);
    if (String(id) === activeId) {
      router.push(pathname);
    }
  }

  return (
    <div className="flex w-64 flex-shrink-0 flex-col rounded-2xl border border-slate-200/80 bg-slate-50/60">
      <div className="p-3">
        <button
          onClick={handleCreate}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          Nouvelle conversation
        </button>
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto px-2 pb-3">
        {isLoading && (
          <p className="px-2 py-4 text-center text-xs text-slate-400">Chargement...</p>
        )}
        {!isLoading && conversations.length === 0 && (
          <p className="px-2 py-4 text-center text-xs text-slate-400">
            Aucune conversation pour l&apos;instant.
          </p>
        )}

        {conversations.map((c) => {
          const isActive = String(c.id) === activeId;
          return (
            <div
              key={c.id}
              onClick={() => handleSelect(c.id)}
              className={cn(
                "group flex cursor-pointer items-start gap-2 rounded-xl border px-3 py-2.5 text-left transition-colors",
                isActive
                  ? "border-blue-100 bg-blue-50"
                  : "border-transparent hover:bg-slate-100"
              )}
            >
              <MessageSquare
                className={cn(
                  "mt-0.5 h-3.5 w-3.5 flex-shrink-0",
                  isActive ? "text-blue-600" : "text-slate-400"
                )}
              />
              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    "truncate text-xs font-semibold",
                    isActive ? "text-blue-700" : "text-slate-700"
                  )}
                >
                  {c.title}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-400">
                  {formatRelativeTime(c.updatedAt)}
                </p>
              </div>
              <button
                onClick={(e) => handleDelete(e, c.id)}
                className="flex-shrink-0 rounded-lg p-1 text-slate-300 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-500 group-hover:opacity-100 cursor-pointer"
                aria-label="Supprimer la conversation"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
