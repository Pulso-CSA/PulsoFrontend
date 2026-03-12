/**
 * Sidebar de chats reutilizável
 * Elemento 08 (Save) para novo chat | Elemento 10 (Delete) para excluir
 */
import { useState, useMemo, useEffect } from "react";
import { MessageSquare, Plus } from "lucide-react";
import { jsPDF } from "jspdf";
import { cn } from "@/lib/utils";
import { CosmicSearchInput } from "@/components/ui/CosmicSearchInput";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

const TRASH_SVG = (
  <svg className="showcase-delete-svg h-3.5 w-3.5 shrink-0" viewBox="0 0 448 512" fill="currentColor" aria-hidden>
    <path d="M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z" />
  </svg>
);

const SAVE_SVG = (
  <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
    <polyline points="17 21 17 13 7 13 7 21" />
    <polyline points="7 3 7 8 15 8" />
  </svg>
);

export interface ChatSessionItem {
  id: string;
  title?: string;
  updatedAt: string;
  messages?: Array<{
    role?: string;
    content?: string;
  }>;
}

interface ChatSidebarProps {
  serviceId: string;
  sessions: ChatSessionItem[];
  currentSessionId: string | null;
  onSelect: (session: ChatSessionItem) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
  onRename?: (session: ChatSessionItem) => void;
  emptyMessage?: string;
}

interface DocumentsFolder {
  id: string;
  name: string;
  chatIds: string[];
}

interface ServiceReportItem {
  id: string;
  filename: string;
  createdAt: string;
  content?: string;
  format?: "txt" | "md";
}

const DEFAULT_SAVED_FOLDER_ID = "pulso-default-saved-folder";
const DEFAULT_SAVED_FOLDER_NAME = "Chats salvos";

function ensureBaseFolders(folders: DocumentsFolder[]): DocumentsFolder[] {
  const safe = Array.isArray(folders) ? folders : [];
  const hasDefault = safe.some((f) => f.id === DEFAULT_SAVED_FOLDER_ID);
  if (hasDefault) return safe;
  return [
    { id: DEFAULT_SAVED_FOLDER_ID, name: DEFAULT_SAVED_FOLDER_NAME, chatIds: [] },
    ...safe,
  ];
}

function getFoldersStorageKey(serviceId: string) {
  return `pulso_docs_folders_${serviceId}`;
}

function getReportsStorageKey(serviceId: string) {
  return `pulso_reports_${serviceId}`;
}

function loadFolders(serviceId: string): DocumentsFolder[] {
  try {
    const raw = localStorage.getItem(getFoldersStorageKey(serviceId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as DocumentsFolder[];
    return ensureBaseFolders(Array.isArray(parsed) ? parsed : []);
  } catch {
    return ensureBaseFolders([]);
  }
}

function persistFolders(serviceId: string, folders: DocumentsFolder[]) {
  localStorage.setItem(getFoldersStorageKey(serviceId), JSON.stringify(folders));
}

function loadReports(serviceId: string): ServiceReportItem[] {
  try {
    const raw = localStorage.getItem(getReportsStorageKey(serviceId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ServiceReportItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function getSessionDisplayName(session: ChatSessionItem): string {
  const rawTitle = (session.title ?? "").trim();
  if (rawTitle && rawTitle.toLowerCase() !== "novo chat") return rawTitle;

  const firstUserMessage = session.messages?.find(
    (m) => m?.role === "user" && typeof m?.content === "string" && m.content.trim().length > 0
  );
  if (firstUserMessage?.content) return firstUserMessage.content.trim().slice(0, 50);

  return `Chat ${session.id.slice(-6)}`;
}

export function ChatSidebar({
  serviceId,
  sessions,
  currentSessionId,
  onSelect,
  onDelete,
  onNewChat,
  emptyMessage = "Nenhum chat ainda",
  onRename,
}: ChatSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showDocuments, setShowDocuments] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [folders, setFolders] = useState<DocumentsFolder[]>(() => loadFolders(serviceId));
  const [reports, setReports] = useState<ServiceReportItem[]>(() => loadReports(serviceId));
  const [reportPreviewOpen, setReportPreviewOpen] = useState(false);
  const [reportPreviewTitle, setReportPreviewTitle] = useState("");
  const [reportPreviewUrl, setReportPreviewUrl] = useState<string | null>(null);
  const [reportPreviewMessage, setReportPreviewMessage] = useState<string | null>(null);

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

  const currentSession = sessions.find((s) => s.id === currentSessionId) ?? null;

  useEffect(() => {
    setFolders(loadFolders(serviceId));
    setReports(loadReports(serviceId));
  }, [serviceId]);

  useEffect(() => {
    return () => {
      if (reportPreviewUrl) URL.revokeObjectURL(reportPreviewUrl);
    };
  }, [reportPreviewUrl]);

  useEffect(() => {
    const onReportsUpdated = (event: Event) => {
      const detail = (event as CustomEvent<{ serviceId?: string }>).detail;
      if (detail?.serviceId !== serviceId) return;
      setReports(loadReports(serviceId));
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key !== getReportsStorageKey(serviceId)) return;
      setReports(loadReports(serviceId));
    };
    window.addEventListener("pulso-reports-updated", onReportsUpdated as EventListener);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("pulso-reports-updated", onReportsUpdated as EventListener);
      window.removeEventListener("storage", onStorage);
    };
  }, [serviceId]);

  const createFolder = () => {
    const name = newFolderName.trim();
    if (!name) return;
    const next: DocumentsFolder[] = ensureBaseFolders([
      ...folders,
      { id: `folder-${crypto.randomUUID()}`, name, chatIds: [] },
    ]);
    setFolders(next);
    persistFolders(serviceId, next);
    setNewFolderName("");
  };

  const deleteFolder = (folderId: string) => {
    if (folderId === DEFAULT_SAVED_FOLDER_ID) return;
    const next = folders.filter((f) => f.id !== folderId);
    setFolders(next);
    persistFolders(serviceId, next);
  };

  const toggleCurrentChatInFolder = (folderId: string) => {
    if (!currentSessionId) return;
    const next = folders.map((f) => {
      if (f.id !== folderId) return f;
      const exists = f.chatIds.includes(currentSessionId);
      return {
        ...f,
        chatIds: exists ? f.chatIds.filter((id) => id !== currentSessionId) : [...f.chatIds, currentSessionId],
      };
    });
    setFolders(next);
    persistFolders(serviceId, next);
  };

  const saveChatToDocuments = (chatId: string) => {
    const alreadySaved = folders.some((f) => f.id === DEFAULT_SAVED_FOLDER_ID && f.chatIds.includes(chatId));
    if (alreadySaved) return;
    const next = ensureBaseFolders(
      folders.map((f) => {
        if (f.id !== DEFAULT_SAVED_FOLDER_ID) return f;
        if (f.chatIds.includes(chatId)) return f;
        return { ...f, chatIds: [...f.chatIds, chatId] };
      })
    );
    setFolders(next);
    persistFolders(serviceId, next);
  };

  const openChatFromDocuments = (chatId: string) => {
    const session = sessions.find((s) => s.id === chatId);
    if (!session) return;
    onSelect(session);
    setShowDocuments(false);
  };

  const openReportPreview = (report: ServiceReportItem) => {
    setReportPreviewTitle(report.filename);
    if (!report.content) {
      setReportPreviewMessage("Este relatório foi gerado em versão anterior e não possui pré-visualização.");
      setReportPreviewOpen(true);
      return;
    }

    const pdf = new jsPDF({ unit: "pt", format: "a4" });
    const marginX = 36;
    const marginY = 42;
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const usableWidth = pageWidth - marginX * 2;
    const usableHeight = pageHeight - marginY * 2;
    const fontSize = 11;
    const lineHeight = 16;

    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(fontSize);

    const lines = pdf.splitTextToSize(report.content, usableWidth) as string[];
    let y = marginY;
    lines.forEach((line) => {
      if (y > marginY + usableHeight) {
        pdf.addPage();
        y = marginY;
      }
      pdf.text(line, marginX, y);
      y += lineHeight;
    });

    const blob = pdf.output("blob");
    if (reportPreviewUrl) URL.revokeObjectURL(reportPreviewUrl);
    const url = URL.createObjectURL(blob);
    setReportPreviewUrl(url);
    setReportPreviewMessage(null);
    setReportPreviewOpen(true);
  };

  return (
    <div className="pulso-chat-sidebar-inner flex h-full min-h-0 flex-col min-w-0">
      <div className="pulso-chat-sidebar-top p-3 border-b border-primary/20 flex items-center justify-between gap-2">
        {/* Botão 3 — Documentos (estilo exato da página inicial) */}
        <button
          type="button"
          onClick={() => setShowDocuments((prev) => !prev)}
          className="showcase-docs-btn pulso-docs-trigger-btn shrink-0"
          aria-label="Documentos"
          title={showDocuments ? "Fechar documentos" : "Abrir documentos"}
        >
          <span className="showcase-folder-container">
            <svg className="showcase-file-back" width="146" height="113" viewBox="0 0 146 113" fill="none" aria-hidden>
              <path d="M0 4C0 1.79086 1.79086 0 4 0H50.3802C51.8285 0 53.2056 0.627965 54.1553 1.72142L64.3303 13.4371C65.2799 14.5306 66.657 15.1585 68.1053 15.1585H141.509C143.718 15.1585 145.509 16.9494 145.509 19.1585V109C145.509 111.209 143.718 113 141.509 113H3.99999C1.79085 113 0 111.209 0 109V4Z" fill="url(#docsBtnBack)" />
              <defs>
                <linearGradient id="docsBtnBack" x1="0" y1="0" x2="72.93" y2="95.4804" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#8F88C2" />
                  <stop offset="1" stopColor="#5C52A2" />
                </linearGradient>
              </defs>
            </svg>
            <svg className="showcase-file-page" width="88" height="99" viewBox="0 0 88 99" fill="none" aria-hidden>
              <rect width="88" height="99" fill="url(#docsBtnPage)" />
              <defs>
                <linearGradient id="docsBtnPage" x1="0" y1="0" x2="81" y2="160.5" gradientUnits="userSpaceOnUse">
                  <stop stopColor="white" />
                  <stop offset="1" stopColor="#686868" />
                </linearGradient>
              </defs>
            </svg>
            <svg className="showcase-file-front" width="160" height="79" viewBox="0 0 160 79" fill="none" aria-hidden>
              <path d="M0.29306 12.2478C0.133905 9.38186 2.41499 6.97059 5.28537 6.97059H30.419H58.1902C59.5751 6.97059 60.9288 6.55982 62.0802 5.79025L68.977 1.18034C70.1283 0.410771 71.482 0 72.8669 0H77H155.462C157.87 0 159.733 2.1129 159.43 4.50232L150.443 75.5023C150.19 77.5013 148.489 79 146.474 79H7.78403C5.66106 79 3.9079 77.3415 3.79019 75.2218L0.29306 12.2478Z" fill="url(#docsBtnFront)" />
              <defs>
                <linearGradient id="docsBtnFront" x1="38.7619" y1="8.71323" x2="66.9106" y2="82.8317" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#C3BBFF" />
                  <stop offset="1" stopColor="#51469A" />
                </linearGradient>
              </defs>
            </svg>
          </span>
          <p className="text-foreground text-sm font-semibold">Documentos</p>
        </button>
        {/* Botão 2 — Novo chat */}
        <button
          type="button"
          onClick={onNewChat}
          className="pulso-new-chat-btn"
          aria-label="Novo chat"
          title="Novo chat"
        >
          <Plus className="pulso-new-chat-btn__icon" />
        </button>
      </div>

      {showDocuments && (
        <div className="pulso-chat-sidebar-top pulso-chat-sidebar-docs p-3 border-b border-primary/10 space-y-3 bg-card/40">
          <div className="showcase-menu-card w-full">
            <div className="px-3 text-xs font-semibold text-foreground">Relatórios</div>
            <div className="showcase-separator" />
            <ul className="showcase-list">
              {reports.length === 0 ? (
                <li className="showcase-element !cursor-default hover:!transform-none hover:!bg-transparent">
                  <span className="text-xs">Sem relatórios neste chat</span>
                </li>
              ) : (
                reports.slice(0, 6).map((report) => (
                  <li
                    key={report.id}
                    className="showcase-element"
                    onClick={() => openReportPreview(report)}
                    title={`Abrir relatório ${report.filename}`}
                  >
                    <span className="text-xs truncate">{report.filename}</span>
                  </li>
                ))
              )}
            </ul>
          </div>

          <div className="showcase-menu-card w-full">
            <div className="px-3 text-xs font-semibold text-foreground">Pastas de chats salvos</div>
            <div className="showcase-separator" />
            <div className="px-3 pb-2 flex items-center gap-2">
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && createFolder()}
                className="showcase-search-input showcase-search-input--compact !h-8 !text-xs !px-2 !w-full"
                placeholder="Nova pasta"
              />
              <button
                type="button"
                onClick={createFolder}
                className="showcase-docs-btn !px-2 !py-1"
                aria-label="Criar pasta"
              >
                <Plus className="h-3.5 w-3.5" />
              </button>
            </div>
            <ul className="showcase-list">
              {folders.length === 0 ? (
                <li className="showcase-element !cursor-default hover:!transform-none hover:!bg-transparent">
                  <span className="text-xs">Crie sua primeira pasta</span>
                </li>
              ) : (
                folders.map((folder) => {
                  const hasCurrentChat = !!currentSessionId && folder.chatIds.includes(currentSessionId);
                  const isFixedFolder = folder.id === DEFAULT_SAVED_FOLDER_ID;
                  return (
                    <li key={folder.id} className="showcase-element !cursor-default hover:!transform-none hover:!bg-transparent !items-start !justify-between overflow-visible">
                      <div className="min-w-0">
                        <p className="text-xs font-medium truncate">{folder.name}</p>
                        <p className="text-[10px] text-muted-foreground">{folder.chatIds.length} chat(s)</p>
                        <button
                          type="button"
                          onClick={() => toggleCurrentChatInFolder(folder.id)}
                          disabled={!currentSessionId}
                          className="mt-1 showcase-docs-btn !py-1 !px-2 !text-[10px] disabled:opacity-50"
                        >
                          {hasCurrentChat
                            ? "Remover chat atual"
                            : `Salvar "${currentSession ? getSessionDisplayName(currentSession) : "chat atual"}"`}
                        </button>
                        {folder.chatIds.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {folder.chatIds.slice(0, 6).map((chatId) => {
                              const session = sessions.find((s) => s.id === chatId);
                              if (!session) return null;
                              return (
                                <button
                                  key={chatId}
                                  type="button"
                                  onClick={() => openChatFromDocuments(chatId)}
                                  className="w-full text-left text-[10px] text-primary hover:underline truncate"
                                  title={`Abrir chat: ${getSessionDisplayName(session)}`}
                                >
                                  {getSessionDisplayName(session)}
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                      {!isFixedFolder && (
                        <button
                          type="button"
                          onClick={() => deleteFolder(folder.id)}
                          className="showcase-delete-btn shrink-0"
                          aria-label={`Excluir pasta ${folder.name}`}
                          title={`Excluir pasta ${folder.name}`}
                        >
                          {TRASH_SVG}
                        </button>
                      )}
                    </li>
                  );
                })
              )}
            </ul>
          </div>
        </div>
      )}

      {/* Barra de busca cosmic (somente lupa à direita) */}
      <div className="pulso-chat-sidebar-top p-2 border-b border-primary/10">
        <CosmicSearchInput
          placeholder="Buscar chats..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="cosmic-search--compact"
        />
      </div>

      <div className="pulso-chat-scroll-area overflow-x-visible p-2 space-y-2">
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
          filteredSessions.map((session) => {
            const isSavedInDocuments = folders.some(
              (f) => f.id === DEFAULT_SAVED_FOLDER_ID && f.chatIds.includes(session.id)
            );

            return (
              <div key={session.id} className="group relative overflow-visible">
                <button
                  onClick={() => onSelect(session)}
                  className={cn(
                    "w-full text-left p-3 rounded-lg transition-all duration-200",
                    currentSessionId === session.id
                      ? "pulso-chat-item-active"
                      : "pulso-chat-item-inactive"
                  )}
                >
                  <p className="text-xs text-foreground line-clamp-2 pr-24">
                    {getSessionDisplayName(session)}
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
                <div className="pulso-chat-item-actions opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      saveChatToDocuments(session.id);
                    }}
                    className={cn(
                      "showcase-save-btn pulso-chat-item-save-btn",
                      isSavedInDocuments && "pulso-chat-item-save-btn--active"
                    )}
                    aria-label="Salvar chat em Documentos"
                    title={isSavedInDocuments ? "Chat já salvo em Documentos" : "Salvar chat em Documentos"}
                  >
                    {SAVE_SVG}
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(session.id);
                    }}
                    className="showcase-delete-btn pulso-chat-item-delete-btn"
                    aria-label="Excluir chat"
                    title="Excluir chat"
                  >
                    {TRASH_SVG}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      <Dialog
        open={reportPreviewOpen}
        onOpenChange={(open) => {
          setReportPreviewOpen(open);
          if (!open) {
            setReportPreviewMessage(null);
          }
        }}
      >
        <DialogContent className="max-w-4xl h-[85vh] p-4">
          <DialogHeader>
            <DialogTitle className="truncate">{reportPreviewTitle || "Relatório"}</DialogTitle>
            <DialogDescription>Pré-visualização em PDF dentro da plataforma.</DialogDescription>
          </DialogHeader>
          <div className="w-full h-full rounded-md border border-primary/20 overflow-hidden bg-background">
            {reportPreviewMessage ? (
              <div className="h-full w-full grid place-items-center p-4 text-sm text-muted-foreground text-center">
                {reportPreviewMessage}
              </div>
            ) : reportPreviewUrl ? (
              <iframe title="Pré-visualização do relatório PDF" src={reportPreviewUrl} className="w-full h-full border-0" />
            ) : (
              <div className="h-full w-full grid place-items-center p-4 text-sm text-muted-foreground text-center">
                Nenhum conteúdo disponível para visualização.
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
