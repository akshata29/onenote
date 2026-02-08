import type { Mode } from "../App";
import { ModeToggle } from "./ModeToggle";

interface Props {
  mode: Mode;
  onModeChange: (m: Mode) => void;
  notebooks: any[];
  sections: any[];
  pages: any[];
  scope: { notebook?: string; section?: string; page?: string };
  onScopeChange: (s: { notebook?: string; section?: string; page?: string }) => void;
}

export function Sidebar({ mode, onModeChange, notebooks, sections, pages, scope, onScopeChange }: Props) {
  const getStringValue = (value: string | undefined): string => {
    if (value === undefined || value === null) {
      return "";
    }
    return value;
  };
  const getOptionalValue = (value: string): string | undefined => {
    if (value === "") {
      return undefined;
    }
    return value;
  };

  return (
    <aside className="bg-panel border-r border-slate-800 min-h-screen flex flex-col p-4 space-y-6">
      <div>
        <p className="text-xs uppercase text-slate-400 mb-2">Mode</p>
        <ModeToggle value={mode} onChange={onModeChange} />
      </div>

      {/* Only show notebook/section selectors in chat modes */}
      {mode !== "admin" && (
        <div className="space-y-3">
          <label className="block text-xs text-slate-400">Notebook</label>
          <select
            value={getStringValue(scope.notebook)}
            onChange={(e) => onScopeChange({ notebook: getOptionalValue(e.target.value) })}
            className="w-full bg-base border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
          >
            <option value="">All notebooks</option>
            {notebooks.map((n) => (
              <option key={n.id} value={n.id}>
                {n.displayName}
              </option>
            ))}
          </select>

          <label className="block text-xs text-slate-400">Section</label>
          <select
            value={getStringValue(scope.section)}
            onChange={(e) => onScopeChange({ ...scope, section: getOptionalValue(e.target.value) })}
            className="w-full bg-base border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
            disabled={!scope.notebook}
          >
            <option value="">All sections</option>
            {sections.map((s) => (
              <option key={s.id} value={s.id}>
                {s.displayName}
              </option>
            ))}
          </select>

          <label className="block text-xs text-slate-400">Page</label>
          <select
            value={getStringValue(scope.page)}
            onChange={(e) => onScopeChange({ ...scope, page: getOptionalValue(e.target.value) })}
            className="w-full bg-base border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
            disabled={!scope.section}
          >
            <option value="">All pages</option>
            {pages.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title ? p.title : p.id}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Admin mode info */}
      {mode === "admin" && (
        <div className="space-y-3">
          <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <p className="text-blue-400 font-medium text-sm mb-2">Admin Panel</p>
            <p className="text-slate-300 text-xs">
              Manage document ingestion, search indexing, and content analysis.
            </p>
          </div>
          
          <div className="space-y-2 text-xs text-slate-400">
            <div className="flex justify-between">
              <span>Total Notebooks:</span>
              <span className="text-slate-300">{notebooks.length}</span>
            </div>
          </div>
        </div>
      )}

      {/* Mode descriptions */}
      {mode !== "admin" && (
        <div className="flex-1 space-y-4">
          {mode === "search" && (
            <div className="p-4 bg-accent/10 border border-accent/20 rounded-lg">
              <p className="text-accent font-medium text-sm mb-2">AI Search Mode</p>
              <p className="text-slate-300 text-xs">
                Search across all your OneNote content using AI-powered semantic search with attachment processing.
              </p>
            </div>
          )}
          
          {mode === "mcp" && (
            <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <p className="text-green-400 font-medium text-sm mb-2">MCP Tool Mode</p>
              <p className="text-slate-300 text-xs">
                Direct access to OneNote content through MCP protocol. Real-time page and section browsing.
              </p>
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
