import { useEffect, useMemo, useState } from "react";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import useSWR from "swr";
import { authFetch, postAuth } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { Sidebar } from "./components/Sidebar";
import { AdminPanel } from "./components/AdminPanel";

export type Mode = "mcp" | "search" | "admin";

function useAccessToken(): string | null {
  const { instance, accounts } = useMsal();
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    const acct = accounts[0];
    if (!acct) {
      console.log("No account found");
      return;
    }
    
    // Wait a bit to ensure MSAL is fully initialized
    setTimeout(async () => {
      console.log("Acquiring token for account:", acct.username);
      try {
        const resp = await instance.acquireTokenSilent({
          scopes: [import.meta.env.VITE_API_SCOPE || "api://your-api-app-id/access_as_user"],
          account: acct,
        });
        console.log("Token acquired silently");
        setToken(resp.accessToken);
      } catch (error) {
        console.log("Silent token acquisition failed:", error);
        try {
          const resp = await instance.acquireTokenPopup({ scopes: [import.meta.env.VITE_API_SCOPE || "api://your-api-app-id/access_as_user"] });
          console.log("Token acquired via popup");
          setToken(resp.accessToken);
        } catch (popupError) {
          console.error("Popup token acquisition failed:", popupError);
        }
      }
    }, 100);
  }, [accounts, instance]);
  return token;
}

const skeleton = <div className="text-slate-300">Loading...</div>;

export default function App() {
  const isAuth = useIsAuthenticated();
  const { instance } = useMsal();
  const token = useAccessToken();
  const [mode, setMode] = useState<Mode>("search");
  const [scope, setScope] = useState<{ notebook?: string; section?: string; page?: string }>({});

  const fetcher = async (url: string) => {
    if (!token) throw new Error("no token yet");
    const response = await authFetch(url, token);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  };

  const { data: notebooks } = useSWR(token ? "/notebooks" : null, fetcher);
  const { data: sections } = useSWR(scope.notebook ? `/notebooks/${scope.notebook}/sections` : null, fetcher);
  const { data: pages } = useSWR(scope.section ? `/sections/${scope.section}/pages` : null, fetcher);

  if (!isAuth) {
    return (
      <main className="min-h-screen flex items-center justify-center text-slate-100">
        <div className="bg-panel border border-slate-700 rounded-2xl p-8 shadow-2xl max-w-md w-full">
          <h1 className="text-2xl font-semibold mb-4">OneNote RAG</h1>
          <p className="text-slate-300 mb-6">Sign in with your work account to chat over OneNote.</p>
          <button
            onClick={() => instance.loginPopup({ scopes: [import.meta.env.VITE_API_SCOPE || "api://your-api-app-id/access_as_user", "User.Read", "Notes.Read"] })}
            className="w-full py-3 bg-accent text-slate-950 font-semibold rounded-lg"
          >
            Sign in with Entra ID
          </button>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen grid grid-cols-[280px_1fr] text-slate-100">
      <Sidebar
        mode={mode}
        onModeChange={setMode}
        notebooks={notebooks?.value || []}
        sections={sections?.value || []}
        pages={pages?.value || []}
        scope={scope}
        onScopeChange={setScope}
      />
      
      {/* Main Content Area */}
      {mode === "admin" ? (
        <AdminPanel 
          token={token} 
          notebooks={notebooks?.value || []} 
        />
      ) : (
        <ChatPanel 
          mode={mode} 
          scope={scope} 
          token={token} 
          notebooks={notebooks?.value || []}
        />
      )}
    </div>
  );
}
