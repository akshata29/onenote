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
  return (
    <aside className="bg-panel border-r border-slate-800 min-h-screen flex flex-col p-4 space-y-6">
      <div>
        <p className="text-xs uppercase text-slate-400 mb-2">Mode</p>
        <ModeToggle value={mode} onChange={onModeChange} />
      </div>

      <div className="space-y-3">
        <label className="block text-xs text-slate-400">Notebook</label>
        <select
          value={scope.notebook ?? ""}
          onChange={(e) => onScopeChange({ notebook: e.target.value || undefined })}
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
          value={scope.section ?? ""}
          onChange={(e) => onScopeChange({ ...scope, section: e.target.value || undefined })}
          className="w-full bg-base border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
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
          value={scope.page ?? ""}
          onChange={(e) => onScopeChange({ ...scope, page: e.target.value || undefined })}
          className="w-full bg-base border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
        >
          <option value="">All pages</option>
          {pages.map((p) => (
            <option key={p.id} value={p.id}>
              {p.title ?? p.id}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-auto space-y-2 text-sm text-slate-400">
        <p className="font-semibold text-slate-200">Admin</p>
        <p className="text-slate-400">Ingestion status and settings are reachable in the Settings page (to be wired).</p>
      </div>
    </aside>
  );
}
