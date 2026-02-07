import type { Mode } from "../App";

interface Props {
  value: Mode;
  onChange: (mode: Mode) => void;
}

export function ModeToggle({ value, onChange }: Props) {
  return (
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
  );
}
