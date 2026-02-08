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
  onRefresh: () => Promise<void>;
  isRefreshing: boolean;
  errors: {
    notebooks?: Error;
    sections?: Error;
    pages?: Error;
  };
}

export function Sidebar({ 
  mode, 
  onModeChange, 
  notebooks, 
  sections, 
  pages, 
  scope, 
  onScopeChange,
  onRefresh,
  isRefreshing,
  errors
}: Props) {
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

      {/* Refresh Controls */}
      <div className="space-y-2">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="w-full py-2 px-3 bg-slate-600 hover:bg-slate-500 disabled:bg-slate-700 disabled:opacity-50 
                     text-slate-100 text-sm font-medium rounded-lg transition-colors
                     flex items-center justify-center gap-2"
        >
          {isRefreshing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-slate-300 border-t-transparent"></div>
              Refreshing...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Data
            </>
          )}
        </button>
        
        {/* Error Display */}
        {(errors.notebooks || errors.sections || errors.pages) && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-red-400 font-medium text-xs mb-1">Connection Issues</p>
            <p className="text-slate-300 text-xs">
              {errors.notebooks?.message.includes('429') || 
               errors.sections?.message.includes('429') || 
               errors.pages?.message.includes('429') 
                ? 'Rate limited. Please wait before refreshing.' 
                : 'Failed to load data. Try refreshing.'}
            </p>
          </div>
        )}
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
