/**
 * Sidebar de chats reutilizável
 * Elemento 08 (Save) para novo chat | Elemento 10 (Delete) para excluir
 */
import { useState, useMemo } from "react";
import { MessageSquare, Bookmark, Folder } from "lucide-react";
import { cn } from "@/lib/utils";
import { CosmicSearchInput } from "@/components/ui/CosmicSearchInput";

const TRASH_SVG = (
  <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 448 512" fill="currentColor" aria-hidden>
    <path d="M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z" />
  </svg>
);

export interface ChatSessionItem {
  id: string;
  title?: string;
  updatedAt: string;
}

interface ChatSidebarProps {
  sessions: ChatSessionItem[];
  currentSessionId: string | null;
  onSelect: (session: ChatSessionItem) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
  onRename?: (session: ChatSessionItem) => void;
  onSavedChats?: () => void;
  onDocuments?: () => void;
  emptyMessage?: string;
}

export function ChatSidebar({
  sessions,
  currentSessionId,
  onSelect,
  onDelete,
  onNewChat,
  onSavedChats,
  onDocuments,
  emptyMessage = "Nenhum chat ainda",
  onRename,
}: ChatSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return [...sessions].reverse();
    const q = searchQuery.toLowerCase();
    return [...sessions]
      .reverse()
      .filter(
        (s) =>
          (s.title || "").toLowerCase().includes(q) ||
          s.id.toLowerCase().includes(q)
      );
  }, [sessions, searchQuery]);

  return (
    <div className="pulso-chat-sidebar-inner flex flex-col min-w-0">
      <div className="p-3 border-b border-primary/20 flex items-center justify-between gap-2">
        {/* Elemento 09 - Botão Documentos (mesmo layout do elemento 09) */}
        <button
          type="button"
          onClick={() => onDocuments?.()}
          className="showcase-docs-btn shrink-0 py-2 px-3 text-xs font-medium text-foreground"
          aria-label="Documentos"
          title="Documentos"
        >
          <Folder className="h-4 w-4 shrink-0" />
          <span>Documentos</span>
        </button>
        <div className="flex items-center gap-2">
          {/* Elemento 09 - Botão Chats salvos (Documents) */}
          <button
            type="button"
            onClick={() => onSavedChats?.()}
            className="showcase-docs-btn shrink-0 py-2 px-3 text-xs font-medium text-foreground"
            aria-label="Chats salvos"
            title="Chats salvos"
          >
            <Bookmark className="h-4 w-4 shrink-0" />
            <span className="hidden sm:inline">Chats salvos</span>
          </button>
          {/* Elemento 08 - Botão Save para criar/salvar novo chat */}
          <button
            type="button"
            onClick={onNewChat}
            className="showcase-save-btn flex items-center justify-center"
            aria-label="Novo chat"
            title="Novo chat"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" data-path="box" />
              <polyline points="17 21 17 13 7 13 7 21" data-path="line-bottom" />
              <polyline points="7 3 7 8 15 8" data-path="line-top" />
            </svg>
          </button>
        </div>
      </div>

      {/* Barra de busca cosmic (lupa) */}
      <div className="p-2 border-b border-primary/10">
        <CosmicSearchInput
          placeholder="Buscar chats..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="cosmic-search--compact cosmic-search--pulso"
        />
      </div>

      <div className="min-h-[400px] overflow-y-hidden overflow-x-hidden p-2 space-y-2 flex-1">
        {filteredSessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4">
            <MessageSquare className="h-8 w-8 text-muted-foreground/30 mb-2" />
            <p className="text-xs text-muted-foreground">
              {sessions.length === 0 ? emptyMessage : "Nenhum resultado encontrado"}
            </p>
            <p className="text-[10px] text-muted-foreground mt-1">
              {sessions.length === 0 ? "Envie uma mensagem para começar" : "Tente outro termo"}
            </p>
          </div>
        ) : (
          filteredSessions.map((session) => (
            <div key={session.id} className="group relative">
              <button
                onClick={() => onSelect(session)}
                className={cn(
                  "w-full text-left p-3 rounded-lg transition-all duration-200",
                  currentSessionId === session.id
                    ? "pulso-chat-item-active"
                    : "pulso-chat-item-inactive"
                )}
              >
                <p className="text-xs text-foreground line-clamp-2 pr-12">
                  {session.title || "Novo chat"}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">
                  {new Date(session.updatedAt).toLocaleString("pt-BR", {
                    day: "2-digit",
                    month: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </button>
              {/* Elemento 10 — botão excluir em círculo glass (mesmo tamanho dos 3 pontinhos) */}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(session.id);
                }}
                className="pulso-chat-item-delete-btn absolute right-1.5 top-1/2 -translate-y-1/2 h-7 w-7 min-h-[28px] min-w-[28px] rounded-full glass border border-border/50 flex items-center justify-center text-foreground hover:text-destructive hover:border-destructive/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                aria-label="Excluir chat"
                title="Excluir chat"
              >
                {TRASH_SVG}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
