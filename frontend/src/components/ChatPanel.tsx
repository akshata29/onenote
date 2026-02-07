import { FormEvent, useMemo, useRef, useState } from "react";
import { postAuth } from "../api";
import type { Mode } from "../App";

interface Props {
  mode: Mode;
  scope: { notebook?: string; section?: string; page?: string };
  token: string | null;
}

export function ChatPanel({ mode, scope, token }: Props) {
  const [messages, setMessages] = useState<{ role: string; content: string; citations?: any[] }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatRef = useRef<HTMLDivElement | null>(null);

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!input || !token) return;
    setLoading(true);
    const newUserMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, newUserMsg]);
    setInput("");
    try {
      const resp = await postAuth<{ answer: string; citations: any[]; mode: string }>(
        "/chat",
        {
          message: newUserMsg.content,
          mode,
          notebook_id: scope.notebook,
          section_id: scope.section,
          page_id: scope.page,
        },
        token
      );
      setMessages((prev) => [...prev, { role: "assistant", content: resp.answer, citations: resp.citations }]);
    } finally {
      setLoading(false);
      chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" });
    }
  };

  const modeLabel = useMemo(() => (mode === "mcp" ? "MCP Tool Mode" : "AI Search Mode"), [mode]);

  return (
    <section className="flex flex-col h-screen bg-base/40 border-l border-slate-800">
      <header className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Mode</p>
          <p className="text-lg font-semibold">{modeLabel}</p>
        </div>
        <span className="px-3 py-1 rounded-full bg-accent/20 text-accent text-sm border border-accent/40">
          {mode.toUpperCase()}
        </span>
      </header>
      <div ref={chatRef} className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m, idx) => (
          <article key={idx} className={`p-4 rounded-xl border ${m.role === "user" ? "border-slate-700 bg-panel" : "border-accent/40 bg-accent/10"}`}>
            <p className="text-sm uppercase tracking-wide text-slate-400 mb-2">{m.role}</p>
            <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
            {m.citations && m.citations.length > 0 && (
              <div className="mt-3 text-xs text-slate-300 space-y-1">
                <p className="font-semibold">Citations</p>
                {m.citations.map((c, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="text-slate-500">•</span>
                    <span>{c.page_title ?? c.page_id ?? "OneNote"}</span>
                  </div>
                ))}
              </div>
            )}
          </article>
        ))}
        {messages.length === 0 && <p className="text-slate-400">Ask anything about your OneNote pages.</p>}
      </div>
      <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-base">
        <div className="rounded-xl border border-slate-700 bg-panel flex items-center px-3">
          <textarea
            className="flex-1 bg-transparent text-slate-100 outline-none py-3 resize-none"
            placeholder="Type a message..."
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            disabled={loading || !input}
            className="px-4 py-2 bg-accent text-slate-950 rounded-lg font-semibold disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </section>
  );
}
