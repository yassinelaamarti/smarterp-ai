import { ChatWindow } from "@/components/chat/ChatWindow";

export default function ChatPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Agent IA</h1>
      <p className="mt-1 text-sm text-slate-500">
        Posez vos questions en langage naturel sur vos données Odoo
      </p>

      <div className="mt-6">
        <ChatWindow />
      </div>
    </div>
  );
}
