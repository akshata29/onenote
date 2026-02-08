import { FormEvent, useMemo, useRef, useState } from "react";
import { postAuth } from "../api";
import { AdvancedSearch } from "./AdvancedSearch";
import type { Mode } from "../App";

interface Props {
  mode: Mode;
  scope: { notebook?: string; section?: string; page?: string };
  token: string | null;
  notebooks?: any[];
}

interface Message {
  role: string;
  content: string;
  citations?: any[];
  metadata?: {
    search_mode?: string;
    filter_applied?: boolean;
    total_results?: number;
  };
}

export function ChatPanel({ mode, scope, token, notebooks = [] }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const chatRef = useRef<HTMLDivElement | null>(null);

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!input || !token) return;
    setLoading(true);
    const newUserMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, newUserMsg]);
    setInput("");
    try {
      const response = await postAuth(
        "/chat",
        {
          message: newUserMsg.content,
          mode,
          notebook_id: scope.notebook,
          section_id: scope.section,
          page_id: scope.page,
          search_mode: "hybrid"
        },
        token
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const resp = await response.json() as { 
        answer: string; 
        citations: any[]; 
        mode: string;
        search_mode?: string;
        filter_applied?: boolean;
        total_results?: number;
      };
      
      const assistantMsg: Message = {
        role: "assistant",
        content: resp.answer,
        citations: resp.citations,
        metadata: {
          search_mode: resp.search_mode,
          filter_applied: resp.filter_applied,
          total_results: resp.total_results
        }
      };
      
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg: Message = {
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : 'Unable to process your request. Please try again.'}`
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" });
    }
  };

  const handleAdvancedSearch = (result: any) => {
    const userMsg: Message = { role: "user", content: result.query || "Advanced search" };
    const assistantMsg: Message = {
      role: "assistant",
      content: result.answer,
      citations: result.citations,
      metadata: {
        search_mode: result.search_mode,
        filter_applied: result.filter_applied,
        total_results: result.total_results
      }
    };
    
    setMessages(prev => [...prev, userMsg, assistantMsg]);
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" });
  };

  const modeLabel = useMemo(() => (mode === "mcp" ? "MCP Tool Mode" : "AI Search Mode"), [mode]);

  return (
    <section className="flex flex-col h-screen bg-base/40 border-l border-slate-800">
      <header className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Mode</p>
            <p className="text-lg font-semibold">{modeLabel}</p>
          </div>
          <span className="px-3 py-1 rounded-full bg-accent/20 text-accent text-sm border border-accent/40">
            {mode.toUpperCase()}
          </span>
        </div>

        {/* Advanced Search Toggle (only in search mode) */}
        {mode === "search" && (
          <div className="flex gap-2">
            <button
              onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
              className={`px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
                showAdvancedSearch
                  ? 'bg-accent/10 border-accent text-accent'
                  : 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {showAdvancedSearch ? 'Simple Search' : 'Advanced Search'}
            </button>
          </div>
        )}

        {/* Advanced Search Interface */}
        {showAdvancedSearch && mode === "search" && (
          <div className="mt-4">
            <AdvancedSearch 
              token={token}
              notebooks={notebooks}
              onSearch={handleAdvancedSearch}
            />
          </div>
        )}
      </header>

      <div ref={chatRef} className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m, idx) => (
          <article key={idx} className={`p-4 rounded-xl border ${m.role === "user" ? "border-slate-700 bg-panel" : "border-accent/40 bg-accent/10"}`}>
            <p className="text-sm uppercase tracking-wide text-slate-400 mb-2">{m.role}</p>
            <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
            
            {/* Search Metadata */}
            {m.metadata && m.role === "assistant" && (
              <div className="mt-3 text-xs text-slate-400 flex gap-4">
                {m.metadata.search_mode && (
                  <span>Mode: {m.metadata.search_mode}</span>
                )}
                {m.metadata.total_results && (
                  <span>Results: {m.metadata.total_results}</span>
                )}
                {m.metadata.filter_applied && (
                  <span className="text-accent">Filtered</span>
                )}
              </div>
            )}
            
            {/* Citations */}
            {m.citations && m.citations.length > 0 && (
              <div className="mt-3 text-xs text-slate-300 space-y-2">
                <p className="font-semibold">Sources</p>
                <div className="space-y-2">
                  {m.citations.map((c, i) => (
                    <div key={i} className="p-2 bg-slate-800/50 rounded border border-slate-700">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-slate-500">•</span>
                        <span className="font-medium">
                          {c.page_title || c.page_id || "OneNote"}
                        </span>
                        {c.content_type === 'attachment' && (
                          <span className="px-1 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                            {c.attachment_filetype?.toUpperCase()}
                          </span>
                        )}
                      </div>
                      {c.notebook_name && (
                        <div className="text-slate-400 text-xs">
                          {c.notebook_name} → {c.section_name}
                        </div>
                      )}
                      {c.attachment_filename && (
                        <div className="text-slate-400 text-xs">
                          📎 {c.attachment_filename}
                        </div>
                      )}
                      {(c.score || c.reranker_score) && (
                        <div className="text-slate-500 text-xs mt-1">
                          {c.reranker_score ? `Relevance: ${(c.reranker_score * 100).toFixed(1)}%` : 
                           c.score ? `Score: ${c.score.toFixed(2)}` : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </article>
        ))}
        {messages.length === 0 && (
          <div className="text-center py-12">
            <p className="text-slate-400 mb-4">Ask anything about your OneNote content.</p>
            {mode === "search" && (
              <p className="text-slate-500 text-sm">
                Try the advanced search for more precise filtering and better results.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Simple Chat Interface (only when not using advanced search) */}
      {(!showAdvancedSearch || mode === "mcp") && (
        <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-base">
          <div className="rounded-xl border border-slate-700 bg-panel flex items-center px-3">
            <textarea
              className="flex-1 bg-transparent text-slate-100 outline-none py-3 resize-none placeholder-slate-400"
              placeholder={mode === "search" ? "Search your OneNote content..." : "Ask about the selected notebooks, sections, or pages..."}
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
            />
            <button
              disabled={loading || !input.trim()}
              className="px-4 py-2 bg-accent text-slate-950 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent/90 transition-colors"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
