import type { Mode } from "../App";

interface Props {
  value: Mode;
  onChange: (mode: Mode) => void;
}

export function ModeToggle({ value, onChange }: Props) {
  return (
    <div className="space-y-2">
      {/* Main modes */}
      <div className="flex rounded-xl border border-slate-700 overflow-hidden">
        <button
          className={`flex-1 px-3 py-2 text-sm font-semibold ${value === "search" ? "bg-accent text-slate-950" : "bg-base text-slate-200"}`}
          onClick={() => onChange("search")}
        >
          AI Search
        </button>
        <button
          className={`flex-1 px-3 py-2 text-sm font-semibold ${value === "mcp" ? "bg-accent text-slate-950" : "bg-base text-slate-200"}`}
          onClick={() => onChange("mcp")}
        >
          MCP Tool
        </button>
      </div>
      
      {/* Admin mode toggle */}
      <button
        className={`w-full px-3 py-2 text-sm font-semibold rounded-lg border ${
          value === "admin" 
            ? "bg-blue-500/20 border-blue-500 text-blue-400" 
            : "bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600"
        }`}
        onClick={() => onChange("admin")}
      >
        🛠️ Admin Panel
      </button>
    </div>
  );
}
